# AUTOGENERATED! DO NOT EDIT! File to edit: 00_core.ipynb (unless otherwise specified).

__all__ = ['md5_update_from_file', 'md5_file', 'md5_update_from_dir', 'md5_dir', 'hashes', 'ProgressParallel',
           'lazy_unpack', 'unpack_body_models', 'fast_amass_unpack', 'viable_slice', 'walk_npz_paths',
           'read_viable_slices', 'global_index_map', 'load_npz', 'AMASS']

# Cell
# https://stackoverflow.com/a/54477583/6937913
import hashlib
from _hashlib import HASH as Hash
from pathlib import Path
from typing import Union


def md5_update_from_file(filename: Union[str, Path], hash: Hash) -> Hash:
    assert Path(filename).is_file()
    with open(str(filename), "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash


def md5_file(filename: Union[str, Path]) -> str:
    return str(md5_update_from_file(filename, hashlib.md5()).hexdigest())


def md5_update_from_dir(directory: Union[str, Path], hash: Hash) -> Hash:
    assert Path(directory).is_dir()
    for path in sorted(Path(directory).iterdir(), key=lambda p: str(p).lower()):
        hash.update(path.name.encode())
        if path.is_file():
            hash = md5_update_from_file(path, hash)
        elif path.is_dir():
            hash = md5_update_from_dir(path, hash)
    return hash


def md5_dir(directory: Union[str, Path]) -> str:
    return str(md5_update_from_dir(directory, hashlib.md5()).hexdigest())

# Cell
hashes = \
{'ACCAD.tar.bz2': {'unpacks_to': 'ACCAD',
  'hash': '193442a2ab66cb116932b8bce08ecb89'},
 'BMLhandball.tar.bz2': {'unpacks_to': 'BMLhandball',
  'hash': '8947df17dd59d052ae618daf24ccace3'},
 'BMLmovi.tar.bz2': {'unpacks_to': 'BMLmovi',
  'hash': '6dfb134273f284152aa2d0838d7529d5'},
 'CMU.tar.bz2': {'unpacks_to': 'CMU',
  'hash': 'f04bc3f37f3eafebfb12ba0cf706ca72'},
 'DFaust67.tar.bz2': {'unpacks_to': 'DFaust_67',
  'hash': '7e5f11ed897da72c5159ef3c747383b8'},
 'EKUT.tar.bz2': {'unpacks_to': 'EKUT',
  'hash': '221ee4a27a03afd1808cbb11af067879'},
 'HumanEva.tar.bz2': {'unpacks_to': 'HumanEva',
  'hash': 'ca781438b08caafd8a42b91cce905a03'},
 'KIT.tar.bz2': {'unpacks_to': 'KIT',
  'hash': '3813500a3909f6ded1a1fffbd27ff35a'},
 'MPIHDM05.tar.bz2': {'unpacks_to': 'MPI_HDM05',
  'hash': 'f76da8deb9e583c65c618d57fbad1be4'},
 'MPILimits.tar.bz2': {'unpacks_to': 'MPI_Limits',
  'hash': '72398ec89ff8ac8550813686cdb07b00'},
 'MPImosh.tar.bz2': {'unpacks_to': 'MPI_mosh',
  'hash': 'a00019cac611816b7ac5b7e2035f3a8a'},
 'SFU.tar.bz2': {'unpacks_to': 'SFU',
  'hash': 'cb10b931509566c0a49d72456e0909e2'},
 'SSMsynced.tar.bz2': {'unpacks_to': 'SSM_synced',
  'hash': '7cc15af6bf95c34e481d58ed04587b58'},
 'TCDhandMocap.tar.bz2': {'unpacks_to': 'TCD_handMocap',
  'hash': 'c500aa07973bf33ac1587a521b7d66d3'},
 'TotalCapture.tar.bz2': {'unpacks_to': 'TotalCapture',
  'hash': 'b2c6833d3341816f4550799b460a1b27'},
 'Transitionsmocap.tar.bz2': {'unpacks_to': 'Transitions_mocap',
  'hash': '705e8020405357d9d65d17580a6e9b39'},
 'EyesJapanDataset.tar.bz2': {'unpacks_to': 'Eyes_Japan_Dataset',
  'hash': 'd19fc19771cfdbe8efe2422719e5f3f1'},
 'BMLrub.tar.bz2': {'unpacks_to': 'BioMotionLab_NTroje',
  'hash': '8b82ffa6c79d42a920f5dde1dcd087c3'},
 'DanceDB.tar.bz2': {'unpacks_to': 'DanceDB',
  'hash': '9ce35953c4234489036ecb1c26ae38bc'}}

# Cell
import json
import argparse
import functools
import os
from shutil import unpack_archive
import joblib
from tqdm.auto import tqdm


class ProgressParallel(joblib.Parallel):
    def __call__(self, *args, **kwargs):
        with tqdm(total=kwargs["total"]) as self._pbar:
            del kwargs["total"]
            return joblib.Parallel.__call__(self, *args, **kwargs)

    def print_progress(self):
        self._pbar.n = self.n_completed_tasks
        self._pbar.refresh()

def lazy_unpack(tarpath, outdir):
    # check if this has already been unpacked by looking for hash file
    tarpath, outdir = Path(tarpath), Path(outdir)
    unpacks_to = hashes[tarpath.name]['unpacks_to']
    hashpath = outdir / Path(unpacks_to+'.hash')
    # if the hash exists and it's correct then assume the directory is correctly unpacked
    if hashpath.exists():
        with open(hashpath) as f:
            h = f.read() # read hash
        if h == hashes[tarpath.name]['hash']:
            return None
    else:
        # if there's no stored hash or it doesn't match, unpack the tar file
        unpack_archive(tarpath, outdir)
        # calculate the hash of the unpacked directory and check it's the same
        h = md5_dir(outdir/unpacks_to)
        _h = hashes[tarpath.name]['hash']
        assert h == _h,\
            f'Directory {outdir/unpacks_to} hash {h} != {_h}'
        # save the calculated hash
        with open(hashpath, 'w') as f:
            f.write(h)

def unpack_body_models(tardir, outdir, n_jobs=1, verify=False):
    tar_root, _, tarfiles = [x for x in os.walk(tardir)][0]
    tarfiles = [x for x in tarfiles if "tar" in x.split(".")]
    tarpaths = [os.path.join(tar_root, tar) for tar in tarfiles]
    for tarpath in tarpaths:
        print(f"{tarpath} extracting to {outdir}")
    unpack = lazy_unpack if verify else unpack_archive
    ProgressParallel(n_jobs=n_jobs)(
        (joblib.delayed(unpack)(tarpath, outdir) for tarpath in tarpaths),
        total=len(tarpaths),
    )


def fast_amass_unpack():
    parser = argparse.ArgumentParser(
        description="Unpack all the body model tar files in a directory to a target directory"
    )
    parser.add_argument(
        "tardir",
        type=str,
        help="Directory containing tar.bz2 body model files",
    )
    parser.add_argument(
        "outdir",
        type=str,
        help="Output directory",
    )
    parser.add_argument(
        "--verify",
        type="store_true",
        help="Verify the output by calculating a checksum, "
        "ensures that each tar file will only be unpacked once."
    )
    parser.add_argument(
        "-n",
        default=1,
        type=int,
        help="Number of jobs to run the tar unpacking with",
    )
    args = parser.parse_args()
    unpack_body_models(args.tardir, args.outdir, n_jobs=args.n, verify=args.verify)

# Cell
import math
import numpy as np
import torch
from torch.utils.data import Dataset
from torch.utils.data import DataLoader

# Cell
def viable_slice(cdata, keep):
    """
    Inspects a dictionary loaded from `.npz` numpy dumps
    and creates a slice of the viable indexes.
    args:

        - `cdata`: dictionary containing keys:
            ['poses', 'gender', 'mocap_framerate', 'betas',
             'marker_data', 'dmpls', 'marker_labels', 'trans']
        - `keep`: ratio of the file to keep, between zero and 1.,
            drops leading and trailing ends of the arrays

    returns:

        - viable: slice that can access frames in the arrays:
            cdata['poses'], cdata['marker_data'], cdata['dmpls'], cdata['trans']
    """
    assert (
        keep > 0.0 and keep <= 1.0
    ), "Proportion of array to keep must be between zero and one"
    n = cdata["poses"].shape[0]
    drop = (1.0 - keep) / 2.0
    return slice(int(n * drop), int(n * keep + n * drop))

# Cell
import warnings


@functools.lru_cache(maxsize=2)
def walk_npz_paths(npz_directory):
    npz_paths = []
    for r, d, f in os.walk(npz_directory):
        npz_files = [x for x in f if "npz" in x.split(".")]
        npz_paths += [os.path.join(npz_directory, r, x) for x in npz_files]
    return tuple(npz_paths)

def read_viable_slices(npz_paths, keep_percent):
    keep = keep_percent/100.
    viable = {}
    for npz_path in npz_paths:
        try:
            # filter out npz files that don't contain pose data
            if Path(npz_path).name not in ['shape.npz']:
                viable[npz_path] = viable_slice(np.load(npz_path), keep=keep)
        except KeyError as err:
            warnings.warn(f'Archive {npz_path} does not contain correctly formatted data')
            # raise Exception(f'Error in archive {npz_path}') from err
    return viable

def global_index_map(npz_directory, overlapping, clip_length, keep=0.8, cache_map=True):
    """
    args:
        - `npz_directory`: Directory containing `.npz` files
        - `overlapping`: Whether clips can overlap
        - `clip_length`:
    returns:
        - map from global index to corresponding file and array indexes
    """
    npz_paths = walk_npz_paths(npz_directory)
    # array slices for each file
    if cache_map:
        cache_map_dir = Path(npz_directory)/Path('viable_slices_memory')
        memory = joblib.Memory(cache_map_dir, verbose=0)
        viable_slices = memory.cache(read_viable_slices)(npz_paths, int(100*keep))
    else:
        viable_slices = read_viable_slices(npz_paths, int(100*keep))
    # clip index -> array index
    def clip_to_array_index(i, array_slice):
        if not overlapping:
            i = i * clip_length
        return [i + array_slice.start + j for j in range(clip_length)]

    # length of a slice
    def lenslice(s):
        if overlapping:
            return (s.stop - s.start) - (clip_length - 1)
        else:
            return math.floor((s.stop - s.start) / clip_length)

    # global index -> file, relative index
    def find_array(i):
        global_index, j = 0, 0
        for npz_path in viable_slices:
            global_index += lenslice(viable_slices[npz_path])
            if i < global_index:
                return npz_path, i - j
            j = global_index

    # how many examples are there in this dataset, total
    n_examples = sum(lenslice(viable_slices[npz_path]) for npz_path in viable_slices)
    # create map function
    def global_to_array(i):
        npz_path, j = find_array(i)
        return npz_path, clip_to_array_index(j, viable_slices[npz_path])

    return global_to_array, n_examples

# Cell
def load_npz(npz_path, indexes, load_poses=True, load_dmpls=True,
             load_trans=True, load_betas=True, load_gender=True):
    # cache this because we will often be accessing the same file multiple times
    cdata = functools.lru_cache(maxsize=128)(np.load)(npz_path)

    data = {}
    # unpack and enforce data type
    if load_poses:
        data['poses'] = cdata["poses"][indexes].astype(np.float32)
    if load_dmpls:
        data['dmpls'] = cdata["dmpls"][indexes].astype(np.float32)
    if load_trans:
        data['trans'] = cdata["trans"][indexes].astype(np.float32)
    if load_betas:
        data['betas'] = np.repeat(
            cdata["betas"][np.newaxis].astype(np.float32), repeats=len(indexes), axis=0
        )
    if load_gender:
        def gender_to_int(g):
            # casting gender to integer will raise a warning in future
            g = str(g.astype(str))
            return {"male": -1, "neutral": 0, "female": 1}[g]
        data['gender'] = np.array([gender_to_int(cdata["gender"]) for _ in indexes])

    return data

# Cell
class AMASS(Dataset):
    def __init__(self, unpacked_directory, clip_length, overlapping,
                 transform=None, memory=False, memory_bytes_limit=None,
                 to_load=('poses', 'dmpls', 'trans', 'betas', 'gender')):
        self.global_to_array, self.n_examples = global_index_map(
            unpacked_directory, overlapping=overlapping, clip_length=clip_length
        )
        self.transform = transform
        self.to_load = {}
        for k in ('poses', 'dmpls', 'trans', 'betas', 'gender'):
            l = f'load_{k}'
            self.to_load[l] = True if k in to_load else False
        caching_directory = Path(unpacked_directory) / Path('memory')
        if memory_bytes_limit is not None:
            warnings.warn(f'AMASS.memory.reduce_size() must be called reduce cache size to be less than {memory_bytes_limit}')
        self.memory = joblib.Memory(caching_directory, verbose=0, bytes_limit=memory_bytes_limit)
        self.load_npz = self.memory.cache(load_npz) if memory else load_npz

    def __len__(self):
        return self.n_examples

    def __getitem__(self, i):
        npz_path, array_index = self.global_to_array(i)
        data = self.load_npz(npz_path, array_index, **self.to_load)
        return {k: self.transform(data[k]) for k in data}