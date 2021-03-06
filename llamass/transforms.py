# AUTOGENERATED! DO NOT EDIT! File to edit: 03_transforms.ipynb (unless otherwise specified).

__all__ = ['rotation_matrix_to_angle_axis', 'rotation_matrix_to_quaternion', 'quaternion_to_angle_axis',
           'angle_axis_to_rotation_matrix', 'Rotation', 'ForwardKinematics', 'SMPL_ForwardKinematics',
           'SMPL_MAJOR_JOINTS', 'SMPL_NR_JOINTS', 'SMPL_PARENTS', 'SMPLHForwardKinematics', 'SMPLH_PARENTS',
           'SMPLH_MAJOR_JOINTS', 'SMPLH_SKELETON', 'scipy_aa_to_euler', 'scipy_euler_to_aa']

# Cell
import torch
import torch.nn.functional as F
import numpy as np
from scipy.spatial.transform import Rotation as R

# Cell
def rotation_matrix_to_angle_axis(rotation_matrix):
    """Convert 3x4 rotation matrix to Rodrigues vector
    Args:
        rotation_matrix (Tensor): rotation matrix.
    Returns:
        Tensor: Rodrigues vector transformation.
    Shape:
        - Input: :math:`(N, 3, 4)`
        - Output: :math:`(N, 3)`
    Example:
        >>> input = torch.rand(2, 3, 4)  # Nx4x4
        >>> output = tgm.rotation_matrix_to_angle_axis(input)  # Nx3
    """
    # todo add check that matrix is a valid rotation matrix
    quaternion = rotation_matrix_to_quaternion(rotation_matrix)
    return quaternion_to_angle_axis(quaternion)

def rotation_matrix_to_quaternion(rotation_matrix, eps=1e-6):
    """Convert 3x4 rotation matrix to 4d quaternion vector
    This algorithm is based on algorithm described in
    https://github.com/KieranWynn/pyquaternion/blob/master/pyquaternion/quaternion.py#L201
    Args:
        rotation_matrix (Tensor): the rotation matrix to convert.
    Return:
        Tensor: the rotation in quaternion
    Shape:
        - Input: :math:`(N, 3, 4)`
        - Output: :math:`(N, 4)`
    Example:
        >>> input = torch.rand(4, 3, 4)  # Nx3x4
        >>> output = tgm.rotation_matrix_to_quaternion(input)  # Nx4
    """
    if not torch.is_tensor(rotation_matrix):
        raise TypeError("Input type is not a torch.Tensor. Got {}".format(
            type(rotation_matrix)))

    if len(rotation_matrix.shape) > 3:
        raise ValueError(
            "Input size must be a three dimensional tensor. Got {}".format(
                rotation_matrix.shape))
    if not rotation_matrix.shape[-2:] == (3, 4):
        raise ValueError(
            "Input size must be a N x 3 x 4  tensor. Got {}".format(
                rotation_matrix.shape))

    rmat_t = torch.transpose(rotation_matrix, 1, 2)

    mask_d2 = rmat_t[:, 2, 2] < eps

    mask_d0_d1 = rmat_t[:, 0, 0] > rmat_t[:, 1, 1]
    mask_d0_nd1 = rmat_t[:, 0, 0] < -rmat_t[:, 1, 1]

    t0 = 1 + rmat_t[:, 0, 0] - rmat_t[:, 1, 1] - rmat_t[:, 2, 2]
    q0 = torch.stack([rmat_t[:, 1, 2] - rmat_t[:, 2, 1],
                      t0, rmat_t[:, 0, 1] + rmat_t[:, 1, 0],
                      rmat_t[:, 2, 0] + rmat_t[:, 0, 2]], -1)
    t0_rep = t0.repeat(4, 1).t()

    t1 = 1 - rmat_t[:, 0, 0] + rmat_t[:, 1, 1] - rmat_t[:, 2, 2]
    q1 = torch.stack([rmat_t[:, 2, 0] - rmat_t[:, 0, 2],
                      rmat_t[:, 0, 1] + rmat_t[:, 1, 0],
                      t1, rmat_t[:, 1, 2] + rmat_t[:, 2, 1]], -1)
    t1_rep = t1.repeat(4, 1).t()

    t2 = 1 - rmat_t[:, 0, 0] - rmat_t[:, 1, 1] + rmat_t[:, 2, 2]
    q2 = torch.stack([rmat_t[:, 0, 1] - rmat_t[:, 1, 0],
                      rmat_t[:, 2, 0] + rmat_t[:, 0, 2],
                      rmat_t[:, 1, 2] + rmat_t[:, 2, 1], t2], -1)
    t2_rep = t2.repeat(4, 1).t()

    t3 = 1 + rmat_t[:, 0, 0] + rmat_t[:, 1, 1] + rmat_t[:, 2, 2]
    q3 = torch.stack([t3, rmat_t[:, 1, 2] - rmat_t[:, 2, 1],
                      rmat_t[:, 2, 0] - rmat_t[:, 0, 2],
                      rmat_t[:, 0, 1] - rmat_t[:, 1, 0]], -1)
    t3_rep = t3.repeat(4, 1).t()

    mask_c0 = mask_d2 * mask_d0_d1
    mask_c1 = mask_d2 * torch.logical_not(mask_d0_d1)
    mask_c2 = torch.logical_not(mask_d2) * mask_d0_nd1
    mask_c3 = torch.logical_not(mask_d2) * torch.logical_not(mask_d0_nd1)
    mask_c0 = mask_c0.view(-1, 1).type_as(q0)
    mask_c1 = mask_c1.view(-1, 1).type_as(q1)
    mask_c2 = mask_c2.view(-1, 1).type_as(q2)
    mask_c3 = mask_c3.view(-1, 1).type_as(q3)

    q = q0 * mask_c0 + q1 * mask_c1 + q2 * mask_c2 + q3 * mask_c3
    q /= torch.sqrt(t0_rep * mask_c0 + t1_rep * mask_c1 +  # noqa
                    t2_rep * mask_c2 + t3_rep * mask_c3)  # noqa
    q *= 0.5
    return q

def quaternion_to_angle_axis(quaternion) -> torch.Tensor:
    """Convert quaternion vector to angle axis of rotation.
    Adapted from ceres C++ library: ceres-solver/include/ceres/rotation.h
    Args:
        quaternion (torch.Tensor): tensor with quaternions.
    Return:
        torch.Tensor: tensor with angle axis of rotation.
    Shape:
        - Input: :math:`(*, 4)` where `*` means, any number of dimensions
        - Output: :math:`(*, 3)`
    Example:
        >>> quaternion = torch.rand(2, 4)  # Nx4
        >>> angle_axis = tgm.quaternion_to_angle_axis(quaternion)  # Nx3
    """
    if not torch.is_tensor(quaternion):
        raise TypeError("Input type is not a torch.Tensor. Got {}".format(
            type(quaternion)))

    if not quaternion.shape[-1] == 4:
        raise ValueError("Input must be a tensor of shape Nx4 or 4. Got {}"
                         .format(quaternion.shape))
    # unpack input and compute conversion
    q1 = quaternion[..., 1]
    q2 = quaternion[..., 2]
    q3 = quaternion[..., 3]
    sin_squared_theta = q1 * q1 + q2 * q2 + q3 * q3

    sin_theta = torch.sqrt(sin_squared_theta)
    cos_theta = quaternion[..., 0]
    two_theta = 2.0 * torch.where(
        cos_theta < 0.0,
        torch.atan2(-sin_theta, -cos_theta),
        torch.atan2(sin_theta, cos_theta))

    k_pos = two_theta / sin_theta
    k_neg = 2.0 * torch.ones_like(sin_theta)
    k = torch.where(sin_squared_theta > 0.0, k_pos, k_neg)

    angle_axis = torch.zeros_like(quaternion)[..., :3]
    angle_axis[..., 0] += q1 * k
    angle_axis[..., 1] += q2 * k
    angle_axis[..., 2] += q3 * k
    return angle_axis

def angle_axis_to_rotation_matrix(angle_axis):
    """Convert 3d vector of axis-angle rotation to 4x4 rotation matrix
    Args:
        angle_axis (Tensor): tensor of 3d vector of axis-angle rotations.
    Returns:
        Tensor: tensor of 4x4 rotation matrices.
    Shape:
        - Input: :math:`(N, 3)`
        - Output: :math:`(N, 4, 4)`
    Example:
        >>> input = torch.rand(1, 3)  # Nx3
        >>> output = tgm.angle_axis_to_rotation_matrix(input)  # Nx4x4
    """
    def _compute_rotation_matrix(angle_axis, theta2, eps=1e-6):
        # We want to be careful to only evaluate the square root if the
        # norm of the angle_axis vector is greater than zero. Otherwise
        # we get a division by zero.
        k_one = 1.0
        theta = torch.sqrt(torch.clamp(theta2, eps, 1e4))
        wxyz = angle_axis / (theta + eps)
        wx, wy, wz = torch.chunk(wxyz, 3, dim=1)
        cos_theta = torch.cos(theta)
        sin_theta = torch.sin(theta)

        r00 = cos_theta + wx * wx * (k_one - cos_theta)
        r10 = wz * sin_theta + wx * wy * (k_one - cos_theta)
        r20 = -wy * sin_theta + wx * wz * (k_one - cos_theta)
        r01 = wx * wy * (k_one - cos_theta) - wz * sin_theta
        r11 = cos_theta + wy * wy * (k_one - cos_theta)
        r21 = wx * sin_theta + wy * wz * (k_one - cos_theta)
        r02 = wy * sin_theta + wx * wz * (k_one - cos_theta)
        r12 = -wx * sin_theta + wy * wz * (k_one - cos_theta)
        r22 = cos_theta + wz * wz * (k_one - cos_theta)
        rotation_matrix = torch.cat(
            [r00, r01, r02, r10, r11, r12, r20, r21, r22], dim=1)
        return rotation_matrix.view(-1, 3, 3)

    def _compute_rotation_matrix_taylor(angle_axis):
        rx, ry, rz = torch.chunk(angle_axis, 3, dim=1)
        k_one = torch.ones_like(rx)
        rotation_matrix = torch.cat(
            [k_one, -rz, ry, rz, k_one, -rx, -ry, rx, k_one], dim=1)
        return rotation_matrix.view(-1, 3, 3)

    # stolen from ceres/rotation.h

    _angle_axis = torch.unsqueeze(angle_axis, dim=1)
    theta2 = torch.matmul(_angle_axis, _angle_axis.transpose(1, 2))
    theta2 = torch.squeeze(theta2, dim=1)

    # compute rotation matrices
    rotation_matrix_normal = _compute_rotation_matrix(angle_axis, theta2)
    rotation_matrix_taylor = _compute_rotation_matrix_taylor(angle_axis)

    # create mask to handle both cases
    eps = 1e-6
    mask = (theta2 > eps).view(-1, 1, 1).to(theta2.device)
    mask_pos = (mask).type_as(theta2)
    mask_neg = (mask == False).type_as(theta2)  # noqa

    # create output pose matrix
    batch_size = angle_axis.shape[0]
    rotation_matrix = torch.eye(4).to(angle_axis.device).type_as(angle_axis)
    rotation_matrix = rotation_matrix.view(1, 4, 4).repeat(batch_size, 1, 1)
    # fill output matrix with masked values
    rotation_matrix[..., :3, :3] = \
        mask_pos * rotation_matrix_normal + mask_neg * rotation_matrix_taylor
    return rotation_matrix  # Nx4x4

# Cell
class Rotation():
    """
    Class to give a scipy.spatial.transform-like interface
    for converting between rotational formalisms in PyTorch.
    Acts on trailing axes and maintains leading tensor shape.
    """
    def __init__(self, tensor, shape, formalism):
        self.tensor, self.shape = tensor, shape
        assert formalism in ['rotvec', 'matrix', 'quat_scalar_first', 'quat_scalar_last']
        self.formalism = formalism

    @staticmethod
    def from_rotvec(x):
        return Rotation(x.view(-1, 3), x.size(), 'rotvec')

    @staticmethod
    def from_matrix(x):
        return Rotation(x.view(-1, 3, 3), x.size(), 'matrix')

    def as_rotvec(self):
        if self.formalism == 'matrix':
            s = self.shape
            if s[-1]%9 == 0:
                new_shape = s[:-1] + (s[-1]//3,)
            elif s[-1]%3 == 0:
                new_shape = s[:-2] + (3,)
            else:
                raise NotImplementedError()
            rotvec = rotation_matrix_to_angle_axis(F.pad(self.tensor, [0,1])) # why is this padded??
            return rotvec.reshape(*new_shape)
        elif self.formalism == 'rotvec':
            return self.tensor.reshape(self.shape)
        elif 'quat' in self.formalism:
            if self.formalism == 'quat_scalar_last':
                perm = torch.tensor([3, 0, 1, 2], dtype=torch.long).to(self.tensor.device)
                self.tensor = self.tensor[:, perm]
            s = self.shape
            rotvec = quaternion_to_angle_axis(quaternion)
            return rotvec.reshape(*s[:-1], 3*s[-1]//4)
        else:
            raise NotImplementedError()

    def as_matrix(self):
        if self.formalism == 'matrix':
            return self.tensor.reshape(self.shape)
        elif self.formalism == 'rotvec':
            s = self.shape
            matrot = angle_axis_to_rotation_matrix(self.tensor)[:, :3, :3].contiguous()
            return matrot.view(*s[:-1], s[-1]*3)
        elif 'quat' in self.formalism:
            self = self.from_rotvec(self.as_rotvec())
            return self.as_matrix()
        else:
            raise NotImplementedError()

    def from_euler(self):
        raise NotImplementedError()

    @staticmethod
    def from_quat(x, scalar_last=True):
        if scalar_last:
            return Rotation(x.view(-1, 4), x.size(), 'quat_scalar_last')
        else:
            return Rotation(x.view(-1, 4), x.size(), 'quat_scalar_first')

    def from_mrp(self):
        raise NotImplementedError()

    def as_euler(self, degrees=False):
        if degrees:
            raise NotImplementedError("Degrees as output not supported.")
        if self.formalism == 'rotvec':
            self = Rotation.from_matrix(self.as_matrix())
        elif self.formalism != 'matrix':
            raise NotImplementedError()
        rs = self.tensor
        n_samples = rs.size(0)

        # initialize to zeros
        e1 = torch.zeros([n_samples]).to(rs.device)
        e2 = torch.zeros([n_samples]).to(rs.device)
        e3 = torch.zeros([n_samples]).to(rs.device)

        # find indices where we need to treat special cases
        is_one = rs[:, 0, 2] == 1
        is_minus_one = rs[:, 0, 2] == -1
        is_special = torch.logical_or(is_one, is_minus_one)

        e1[is_special] = torch.atan2(rs[is_special, 0, 1], rs[is_special, 0, 2])
        e2[is_minus_one] = np.pi/2
        e2[is_one] = -np.pi/2

        # normal cases
        is_normal = torch.logical_not(torch.logical_or(is_one, is_minus_one))
        # clip inputs to arcsin
        in_ = torch.clamp(rs[is_normal, 0, 2], -1, 1)
        e2[is_normal] = -torch.arcsin(in_)
        e2_cos = torch.cos(e2[is_normal])
        e1[is_normal] = torch.atan2(rs[is_normal, 1, 2]/e2_cos,
                                    rs[is_normal, 2, 2]/e2_cos)
        e3[is_normal] = torch.atan2(rs[is_normal, 0, 1]/e2_cos,
                                    rs[is_normal, 0, 0]/e2_cos)

        eul = torch.stack([e1, e2, e3], axis=-1)
        #eul = np.reshape(eul, np.concatenate([orig_shape, eul.shape[1:]]))
        s = self.shape
        eul = eul.reshape(*s[:-1], s[-1]//3)
        return eul

    @staticmethod
    def _to_scalar_last(x):
        perm = torch.tensor([1, 2, 3, 0], dtype=torch.long).to(x.device)
        return x[:, perm]

    def as_quat(self):
        if 'quat' in self.formalism:
            if self.formalism == 'quat_scalar_first':
                self.tensor = self._to_scalar_last(self.tensor)
            return self.tensor.reshape(self.shape)
        elif self.formalism == 'rotvec':
            self = Rotation.from_matrix(self.as_matrix())
        assert self.formalism == 'matrix'
        s = self.shape
        if s[-1]%9 == 0:
            new_shape = s[:-1] + (4*s[-1]//9,)
        elif s[-1] == 3:
            new_shape = s[:-2] + (4,)
        quat = rotation_matrix_to_quaternion(F.pad(self.tensor, [0,1]))
        quat = self._to_scalar_last(quat)
        return quat.reshape(*new_shape)

    def as_mrp(self):
        raise NotImplementedError()

# Cell
"""
PyTorch port of forward kinematics engine from:
SPL: training and evaluation of neural networks with a structured prediction layer.
Copyright (C) 2021 ETH Zurich, Emre Aksan, Manuel Kaufmann, Gavin Gray

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import torch.nn as nn

class ForwardKinematics(nn.Module):
    def __init__(self, offsets, parents, left_mult=False, major_joints=None, norm_idx=None, no_root=True):
        super(ForwardKinematics, self).__init__()
        self.register_buffer('offsets', offsets)
        if norm_idx is not None:
            self.offsets = self.offsets / np.linalg.norm(self.offsets[norm_idx])
        self.parents = parents
        self.n_joints = len(parents)
        self.major_joints = major_joints
        self.left_mult = left_mult
        self.no_root = no_root
        assert self.offsets.shape[0] == self.n_joints

    def fk(self, joint_angles):
        """
        Perform forward kinematics. This requires joint angles to be in rotation matrix format.
        Args:
            joint_angles: torch tensor of shape (N, n_joints*3*3)
        Returns:
            The 3D joint positions as a tensor of shape (N, n_joints, 3)
        """
        assert joint_angles.shape[-1] == self.n_joints * 9
        angles = joint_angles.view(-1, self.n_joints, 3, 3)
        n_frames = angles.size(0)
        device = angles.device
        if self.left_mult:
            offsets = self.offsets.view(1, 1, self.n_joints, 3)
        else:
            offsets = self.offsets.view(1, self.n_joints, 3, 1)

        if self.no_root:
            angles[:, 0] = torch.eye(3).to(device)

        assert self.parents[0] == -1
        positions = {0: torch.zeros([n_frames, 3]).to(device)}
        rotations = {0: angles[:, 0]}

        for j in range(1, self.n_joints):
            prev_rotation = rotations[self.parents[j]]
            prev_position = positions[self.parents[j]]
            # this is a regular joint
            if self.left_mult:
                position = torch.squeeze(torch.matmul(offsets[:, :, j], prev_rotation)) + prev_position
                rotation = torch.matmul(angles[:, j], prev_rotation)
            else:
                position = torch.squeeze(torch.matmul(prev_rotation, offsets[:, j])) + prev_position
                rotation =  torch.matmul(prev_rotation, angles[:, j])
            positions[j] = position
            rotations[j] = rotation

        return torch.cat([positions[j].view(n_frames, 1, 3) for j in range(self.n_joints)], 1)

    def from_aa(self, joint_angles):
        """
        Get joint positions from angle axis representations in shape (N, n_joints*3).
        """
        angles_rot = Rotation.from_rotvec(joint_angles).as_matrix()
        return self.fk(torch.reshape(angles_rot, [-1, self.n_joints * 9]))

    def from_rotmat(self, joint_angles):
        """
        Get joint positions from rotation matrix representations in shape (N, n_joints*3*3).
        """
        return self.fk(joint_angles)

    def from_quat(self, joint_angles):
        raise NotImplementedError()

    def from_sparse(self, joint_angles_sparse, rep="rotmat", return_sparse=True):
        raise NotImplementedError()

# Cell
SMPL_MAJOR_JOINTS = [1, 2, 3, 4, 5, 6, 9, 12, 13, 14, 15, 16, 17, 18, 19]
SMPL_NR_JOINTS = 24
SMPL_PARENTS = [-1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 12, 13, 14, 16, 17, 18, 19, 20, 21]


class SMPL_ForwardKinematics(ForwardKinematics):
    """
    Forward Kinematics for the skeleton defined by SMPL.
    """
    def __init__(self):
        # this are the offsets stored under `J` in the SMPL model pickle file
        offsets = torch.tensor([[-8.76308970e-04, -2.11418723e-01, 2.78211200e-02],
                            [7.04848876e-02, -3.01002533e-01, 1.97749280e-02],
                            [-6.98883278e-02, -3.00379160e-01, 2.30254335e-02],
                            [-3.38451650e-03, -1.08161861e-01, 5.63597909e-03],
                            [1.01153808e-01, -6.65211904e-01, 1.30860155e-02],
                            [-1.06040718e-01, -6.71029623e-01, 1.38401121e-02],
                            [1.96440985e-04, 1.94957852e-02, 3.92296547e-03],
                            [8.95999143e-02, -1.04856032e+00, -3.04155922e-02],
                            [-9.20120818e-02, -1.05466743e+00, -2.80514913e-02],
                            [2.22362284e-03, 6.85680141e-02, 3.17901760e-02],
                            [1.12937580e-01, -1.10320516e+00, 8.39545265e-02],
                            [-1.14055299e-01, -1.10107698e+00, 8.98482216e-02],
                            [2.60992373e-04, 2.76811197e-01, -1.79753042e-02],
                            [7.75218998e-02, 1.86348444e-01, -5.08464100e-03],
                            [-7.48091986e-02, 1.84174211e-01, -1.00204779e-02],
                            [3.77815350e-03, 3.39133394e-01, 3.22299558e-02],
                            [1.62839013e-01, 2.18087461e-01, -1.23774789e-02],
                            [-1.64012068e-01, 2.16959041e-01, -1.98226746e-02],
                            [4.14086325e-01, 2.06120683e-01, -3.98959248e-02],
                            [-4.10001734e-01, 2.03806676e-01, -3.99843890e-02],
                            [6.52105424e-01, 2.15127546e-01, -3.98521818e-02],
                            [-6.55178550e-01, 2.12428626e-01, -4.35159074e-02],
                            [7.31773168e-01, 2.05445019e-01, -5.30577698e-02],
                            [-7.35578759e-01, 2.05180646e-01, -5.39352281e-02]])

        # need to convert them to compatible offsets
        smpl_offsets = torch.zeros([24, 3])
        smpl_offsets[0] = offsets[0]
        for idx, pid in enumerate(SMPL_PARENTS[1:]):
            smpl_offsets[idx+1] = offsets[idx + 1] - offsets[pid]

        # normalize so that right thigh has length 1
        super(SMPL_ForwardKinematics, self).__init__(smpl_offsets, SMPL_PARENTS, norm_idx=4,
                                                    left_mult=False, major_joints=SMPL_MAJOR_JOINTS)

# Cell
SMPLH_PARENTS = [-1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 12, 13, 14, 16, 17, 18, 19, 20, 21]
SMPLH_MAJOR_JOINTS = [1, 2, 3, 4, 5, 6, 9, 12, 13, 14, 15, 16, 17, 18, 19]
SMPLH_SKELETON = np.array([
    [ 0,  0,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9,  9,  9, 12, 13, 14, 16, 17, 18, 19, 20, 21],
    [ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
]).T

class SMPLHForwardKinematics(ForwardKinematics):
    """
    Forward Kinematics for the skeleton defined by SMPL-H.
    """
    def __init__(self):
        # this are the offsets stored under `J` in the SMPL model pickle file
        offsets = torch.tensor([[-1.79505953e-03, -2.23333446e-01,  2.82191255e-02],
                           [ 6.77246757e-02, -3.14739671e-01,  2.14037877e-02],
                           [-6.94655406e-02, -3.13855126e-01,  2.38993038e-02],
                           [-4.32792313e-03, -1.14370215e-01,  1.52281192e-03],
                           [ 1.02001221e-01, -6.89938274e-01,  1.69079858e-02],
                           [-1.07755594e-01, -6.96424140e-01,  1.50492738e-02],
                           [ 1.15910534e-03,  2.08102144e-02,  2.61528404e-03],
                           [ 8.84055199e-02, -1.08789863e+00, -2.67853442e-02],
                           [-9.19818258e-02, -1.09483879e+00, -2.72625243e-02],
                           [ 2.61610388e-03,  7.37324481e-02,  2.80398521e-02],
                           [ 1.14763659e-01, -1.14368952e+00,  9.25030544e-02],
                           [-1.17353574e-01, -1.14298274e+00,  9.60854266e-02],
                           [-1.62284535e-04,  2.87602804e-01, -1.48171829e-02],
                           [ 8.14608431e-02,  1.95481750e-01, -6.04975478e-03],
                           [-7.91430834e-02,  1.92565283e-01, -1.05754332e-02],
                           [ 4.98955543e-03,  3.52572414e-01,  3.65317875e-02],
                           [ 1.72437770e-01,  2.25950646e-01, -1.49179062e-02],
                           [-1.75155461e-01,  2.25116450e-01, -1.97185045e-02],
                           [ 4.32050017e-01,  2.13178586e-01, -4.23743412e-02],
                           [-4.28897421e-01,  2.11787231e-01, -4.11194829e-02],
                           [ 6.81283645e-01,  2.22164620e-01, -4.35452575e-02],
                           [-6.84195501e-01,  2.19559526e-01, -4.66786778e-02],
                           [ 7.65325829e-01,  2.14003084e-01, -5.84906248e-02],
                           [-7.68817426e-01,  2.13442268e-01, -5.69937621e-02]])

        # need to convert them to compatible offsets
        smplh_offsets = torch.zeros([24, 3])
        smplh_offsets[0] = offsets[0]
        for idx, pid in enumerate(SMPLH_PARENTS[1:]):
            smplh_offsets[idx+1] = offsets[idx + 1] - offsets[pid]

        # normalize so that right thigh has length 1
        super(SMPLHForwardKinematics, self).__init__(smplh_offsets, SMPLH_PARENTS, norm_idx=4,
                                                    left_mult=False, major_joints=SMPLH_MAJOR_JOINTS)

# Cell
import math

def scipy_aa_to_euler(x, seq='zyx'):
    s = x.shape
    x = x.reshape(-1, 3)
    euler = R.from_rotvec(x).as_euler(seq)
    return euler.reshape(*s)

def scipy_euler_to_aa(x, seq='zyx'):
    s = x.shape
    x = x.reshape(-1, 3)
    aa = R.from_euler(seq, x).as_rotvec()
    return aa.reshape(*s)