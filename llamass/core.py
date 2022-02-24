# AUTOGENERATED! DO NOT EDIT! File to edit: 00_core.ipynb (unless otherwise specified).

__all__ = ['md5_update_from_file', 'md5_file', 'md5_update_from_dir', 'md5_dir', 'hashes', 'lazy_unpack',
           'unpack_body_models', 'fast_amass_unpack', 'npz_paths', 'npz_len', 'npz_lens', 'save_lens', 'keep_slice',
           'viable_slice', 'npz_contents', 'AMASS', 'worker_init_fn', 'IterableLoader', 'amass_splits',
           'move_dirs_into_splits', 'move_dirs_out_of_splits', 'console_split_dirs', 'spl_splits', 'write_to_lmdb',
           'AMASSdb', 'amass_to_lmdb', 'console_amass_to_lmdb']

# Cell
# https://stackoverflow.com/a/54477583/6937913
# function to evaluate the hash of an entire directory system to verify downloading and unpacking was correct
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
hashes = {
    "ACCAD.tar.bz2": {
        "unpacks_to": "ACCAD",
        "hash": "193442a2ab66cb116932b8bce08ecb89",
    },
    "BMLhandball.tar.bz2": {
        "unpacks_to": "BMLhandball",
        "hash": "8947df17dd59d052ae618daf24ccace3",
    },
    "BMLmovi.tar.bz2": {
        "unpacks_to": "BMLmovi",
        "hash": "6dfb134273f284152aa2d0838d7529d5",
    },
    "CMU.tar.bz2": {"unpacks_to": "CMU", "hash": "f04bc3f37f3eafebfb12ba0cf706ca72"},
    "DFaust67.tar.bz2": {
        "unpacks_to": "DFaust_67",
        "hash": "7e5f11ed897da72c5159ef3c747383b8",
    },
    "EKUT.tar.bz2": {"unpacks_to": "EKUT", "hash": "221ee4a27a03afd1808cbb11af067879"},
    "HumanEva.tar.bz2": {
        "unpacks_to": "HumanEva",
        "hash": "ca781438b08caafd8a42b91cce905a03",
    },
    "KIT.tar.bz2": {"unpacks_to": "KIT", "hash": "3813500a3909f6ded1a1fffbd27ff35a"},
    "MPIHDM05.tar.bz2": {
        "unpacks_to": "MPI_HDM05",
        "hash": "f76da8deb9e583c65c618d57fbad1be4",
    },
    "MPILimits.tar.bz2": {
        "unpacks_to": "MPI_Limits",
        "hash": "72398ec89ff8ac8550813686cdb07b00",
    },
    "MPImosh.tar.bz2": {
        "unpacks_to": "MPI_mosh",
        "hash": "a00019cac611816b7ac5b7e2035f3a8a",
    },
    "SFU.tar.bz2": {"unpacks_to": "SFU", "hash": "cb10b931509566c0a49d72456e0909e2"},
    "SSMsynced.tar.bz2": {
        "unpacks_to": "SSM_synced",
        "hash": "7cc15af6bf95c34e481d58ed04587b58",
    },
    "TCDhandMocap.tar.bz2": {
        "unpacks_to": "TCD_handMocap",
        "hash": "c500aa07973bf33ac1587a521b7d66d3",
    },
    "TotalCapture.tar.bz2": {
        "unpacks_to": "TotalCapture",
        "hash": "b2c6833d3341816f4550799b460a1b27",
    },
    "Transitionsmocap.tar.bz2": {
        "unpacks_to": "Transitions_mocap",
        "hash": "705e8020405357d9d65d17580a6e9b39",
    },
    "EyesJapanDataset.tar.bz2": {
        "unpacks_to": "Eyes_Japan_Dataset",
        "hash": "d19fc19771cfdbe8efe2422719e5f3f1",
    },
    "BMLrub.tar.bz2": {
        "unpacks_to": "BioMotionLab_NTroje",
        "hash": "8b82ffa6c79d42a920f5dde1dcd087c3",
    },
    "DanceDB.tar.bz2": {
        "unpacks_to": "DanceDB",
        "hash": "9ce35953c4234489036ecb1c26ae38bc",
    },
}

# Cell
import json
import argparse
import functools
import os
from shutil import unpack_archive
import joblib
from tqdm.auto import tqdm
from .tqdm import ProgressParallel


def lazy_unpack(tarpath, outdir):
    # check if this has already been unpacked by looking for hash file
    tarpath, outdir = Path(tarpath), Path(outdir)
    unpacks_to = hashes[tarpath.name]["unpacks_to"]
    hashpath = outdir / Path(unpacks_to + ".hash")
    # if the hash exists and it's correct then assume the directory is correctly unpacked
    if hashpath.exists():
        with open(hashpath) as f:
            h = f.read()  # read hash
        if h == hashes[tarpath.name]["hash"]:
            return None
    else:
        # if there's no stored hash or it doesn't match, unpack the tar file
        unpack_archive(tarpath, outdir)
        # calculate the hash of the unpacked directory and check it's the same
        h = md5_dir(outdir / unpacks_to)
        _h = hashes[tarpath.name]["hash"]
        assert h == _h, f"Directory {outdir/unpacks_to} hash {h} != {_h}"
        # save the calculated hash
        with open(hashpath, "w") as f:
            f.write(h)


def unpack_body_models(tardir, outdir, n_jobs=1, verify=False, verbose=False):
    tar_root, _, tarfiles = [x for x in os.walk(tardir)][0]
    tarfiles = [x for x in tarfiles if "tar" in x.split(".")]
    tarpaths = [os.path.join(tar_root, tar) for tar in tarfiles]
    for tarpath in tarpaths:
        if verbose:
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
        action="store_true",
        help="Verify the output by calculating a checksum, "
        "ensures that each tar file will only be unpacked once.",
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
import gzip
import json
import random
import math
import warnings
import numpy as np
import torch
import torch.utils.data as tudata

# Cell
def npz_paths(npz_directory):
    npz_directory = Path(npz_directory).resolve()
    npz_paths = []
    for r, d, f in os.walk(npz_directory, followlinks=True):
        for fname in f:
            if "npz" == fname.split(".")[-1] and fname != "shape.npz":
                yield os.path.join(npz_directory, r, fname)

# Cell
def npz_len(npz_path, strict=True):
    cdata = np.load(npz_path)
    h = md5_file(npz_path)
    dirs = [hashes[h]['unpacks_to'] for h in hashes]
    if strict:
        m = []
        for p in Path(npz_path).parents:
            m += [d for d in dirs if p.name == d]
        assert len(m) == 1, f"Subdir of {npz_path} contains {len(m)} of {dirs}"
        subdir = m[0]
    else:
        subdir = Path(npz_path).parts[-2]
    return subdir, h, cdata["poses"].shape[0]

def npz_lens(unpacked_directory, n_jobs, strict=True):
    paths = [p for p in npz_paths(unpacked_directory)]
    return ProgressParallel(n_jobs=n_jobs)(
        [joblib.delayed(npz_len)(npz_path, strict=strict) for npz_path in paths], total=len(paths)
    )

def save_lens(save_path, npz_file_lens):
    with gzip.open(save_path, "wt") as f:
        f.write(json.dumps(npz_file_lens))

#npz_file_lens = npz_lens('/nobackup/gngdb/repos/amass/data', 10)
#save_lens('npz_file_lens.json.gz', npz_file_lens)

# Cell
def keep_slice(n, keep):
    drop = (1.0 - keep) / 2.0
    return slice(int(n * drop), int(n * keep + n * drop))


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
    return keep_slice(n, keep)

# Cell
def npz_contents(
    npz_path,
    clip_length,
    overlapping,
    keep=0.8,
    keys=("poses", "dmpls", "trans", "betas", "gender"),
    shuffle=False,
    seed=None,
):
    # cache this because we will often be accessing the same file multiple times
    cdata = np.load(npz_path)

    # slice of viable indices
    viable = viable_slice(cdata, keep)

    # slice iterator
    # every time the file is opened the non-overlapping slices will be the same
    # this may not be preferred, but loading overlapping means a lot of repetitive data
    def clip_slices(viable, clip_length, overlapping):
        i = 0
        step = 1 if overlapping else clip_length
        for i in range(viable.start, viable.stop, step):
            if i + clip_length < viable.stop:
                yield slice(i, i + clip_length)

    # buffer the iterator and shuffle here, when implementing that
    buf_clip_slices = [s for s in clip_slices(viable, clip_length, overlapping)]
    if shuffle:
        # this will be correlated over workers
        # seed should be passed drawn from torch Generator
        seed = seed if seed else random.randint(1e6)
        random.Random(seed).shuffle(buf_clip_slices)

    # iterate over slices
    for s in buf_clip_slices:
        data = {}
        # unpack and enforce data type
        to_load = [k for k in ("poses", "dmpls", "trans") if k in keys]
        for k in to_load:
            data[k] = cdata[k][s].astype(np.float32)
        if "betas" in keys:
            r = s.stop - s.start
            data["betas"] = np.repeat(
                cdata["betas"][np.newaxis].astype(np.float32), repeats=r, axis=0
            )
        if "gender" in keys:

            def gender_to_int(g):
                # casting gender to integer will raise a warning in future
                g = str(g.astype(str))
                return {"male": -1, "neutral": 0, "female": 1}[g]

            data["gender"] = np.array(
                [gender_to_int(cdata["gender"]) for _ in range(s.start, s.stop)]
            )
        yield data

# Cell
class AMASS(tudata.IterableDataset):
    def __init__(
        self,
        amass_location,
        clip_length,
        overlapping,
        keep=0.8,
        transform=None,
        data_keys=("poses", "dmpls", "trans", "betas", "gender"),
        file_list_seed=0,
        shuffle=False,
        seed=None,
        strict=True
    ):
        assert clip_length > 0 and type(clip_length) is int
        self.transform = transform
        self.data_keys = data_keys
        self.amass_location = amass_location
        # these should be shuffled but pull shuffle argument out of dataloader worker arguments
        self._npz_paths = [npz_path for npz_path in npz_paths(amass_location)]
        random.Random(file_list_seed).shuffle(self._npz_paths)
        self._npz_paths = tuple(self._npz_paths)
        self.npz_paths = self._npz_paths
        self.clip_length = clip_length
        self.overlapping = overlapping
        self.keep = keep
        self.shuffle = shuffle
        self.seed = seed if seed else random.randint(0, 1e6)
        self.strict = strict

    def infer_len(self, n_jobs=4):
        # uses known dimensions of the npz files in the AMASS dataset to infer the length
        # with clip_length and overlapping settings stored
        lenfile = Path(self.amass_location) / Path("npz_file_lens.json.gz")
        # try to load file
        if lenfile.exists():
            with gzip.open(lenfile, "rt") as f:
                self.npz_lens = json.load(f)
                def filter_lens(npz_lens):
                    # filter out file length information to only existing dirs
                    datasets = [p.name for p in Path(self.amass_location).glob('*') if p.is_dir()]
                    return [(p, h, l) for p, h, l in npz_lens
                            if p in datasets]
                self.npz_lens = filter_lens(self.npz_lens)
        else:  # if it's not there, recompute it and create the file
            print(f'Inspecting {len(self.npz_paths)} files to determine dataset length'
                  f', saving the result to {lenfile}')
            self.npz_lens = npz_lens(self.amass_location, n_jobs, strict=self.strict)
            save_lens(lenfile, self.npz_lens)

        # using stored lengths to infer the total dataset length
        def lenslice(s):
            if self.overlapping:
                return (s.stop - s.start) - (self.clip_length - 1)
            else:
                return math.floor((s.stop - s.start) / self.clip_length)

        N = 0
        for p, h, l in self.npz_lens:
            s = keep_slice(l, keep=self.keep)
            N += lenslice(s)

        return N

    def __len__(self):
        if hasattr(self, "N"):
            return self.N
        else:
            self.N = self.infer_len()
            return self.N

    def __iter__(self):
        if self.shuffle:
            self.npz_paths = list(self.npz_paths)
            random.Random(self.seed).shuffle(self.npz_paths)
        for npz_path in self.npz_paths:
            for data in npz_contents(
                npz_path,
                self.clip_length,
                self.overlapping,
                keys=self.data_keys,
                keep=self.keep,
                shuffle=self.shuffle,
                seed=self.seed,
            ):
                self.seed += 1  # increment to vary shuffle over files
                yield {k: self.transform(data[k]) for k in data}

# Cell
def worker_init_fn(worker_id):
    worker_info = torch.utils.data.get_worker_info()

    # slice up dataset among workers
    dataset = worker_info.dataset
    overall_npz_paths = dataset._npz_paths
    step = int(len(overall_npz_paths) / float(worker_info.num_workers))
    n = len(overall_npz_paths)
    assert n >= worker_info.num_workers, (
        "Every worker must get at least one file:" f" {worker_info.num_workers} > {n}"
    )
    start, stop = 0, n
    for worker_idx, i in enumerate(range(start, stop, step)):
        if worker_idx == worker_info.id:
            worker_slice = slice(i, min(i + step, n + 1))
    dataset.npz_paths = overall_npz_paths[worker_slice]

    # set each workers seed
    dataset.seed = dataset.seed + worker_info.seed

class IterableLoader(tudata.DataLoader):
    def __init__(self, *args, **kwargs):
        kwargs['worker_init_fn'] = worker_init_fn
        super().__init__(*args, **kwargs)

# Cell
amass_splits = {
    'val' : ['HumanEva', 'MPI_HDM05', 'SFU', 'MPI_mosh'],
    'test': ['Transitions_mocap', 'SSM_synced'],
    'train': ['CMU', 'MPI_Limits', 'TotalCapture', 'Eyes_Japan_Dataset',
              'KIT', 'BML', 'EKUT', 'TCD_handMocap', 'ACCAD',
              'BMLmovi', 'BioMotionLab_NTroje', 'DanceDB', 'BMLhandball', 'DFaust_67']
}

# Cell
def move_dirs_into_splits(amass_loc, splits, undo=False):
    amass_loc = Path(amass_loc)
    for k in amass_splits:
        split_dir = amass_loc / Path(k)
        if not split_dir.exists():
            os.mkdir(split_dir)
        for d in amass_splits[k]:
            d = Path(d)
            t = split_dir/d
            f = amass_loc/d
            try:
                if undo:
                    os.rename(t, f)
                else:
                    os.rename(f, t)
            except FileNotFoundError:
                warnings.warn(f'Could not find {d} for {k} split')

move_dirs_out_of_splits = functools.partial(move_dirs_into_splits, undo=True)

# Cell
def console_split_dirs():
    parser = argparse.ArgumentParser(
        description="Split AMASS Dataset subdirs into train/val/test"
    )
    parser.add_argument(
        "amassloc",
        type=str,
        help="Location where AMASS has been unpacked",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Undo move into subdirectories, put them all back in the root AMASS location",
    )
    args = parser.parse_args()
    move_dirs_into_splits(args.amassloc, amass_splits, undo=args.undo)

# Cell
spl_splits = dict(
    training  =  {'CMU_Kitchen', 'Eyes', 'HEva', '', 'MIXAMO', 'Transition', 'CMU', 'SSM', 'BioMotion', 'JointLimit', 'ACCAD', 'HDM05'},
    validation  =  {'Eyes', '', 'MIXAMO', 'Transition', 'CMU', 'SSM', 'BioMotion', 'JointLimit', 'ACCAD', 'HDM05'},
    test  =  {'CMU_Kitchen', 'Eyes', 'HEva', '', 'MIXAMO', 'Transition', 'CMU', 'BioMotion', 'JointLimit', 'ACCAD', 'HDM05'}
)

# Cell
import dataflow as td


def write_to_lmdb(dataset, batch_size, num_workers=0, prefetch_factor=4):
    overlapping = 'overlapping' if dataset.overlapping else 'separated'
    db_filename = f'amass-{dataset.clip_length}-{overlapping}.lmdb'
    db_loc = os.path.join(dataset.amass_location, db_filename)
    def collate_fn(data):
        return data
    amassloader = tudata.DataLoader(
        dataset,
        batch_size=batch_size,
        worker_init_fn=worker_init_fn,
        num_workers=num_workers,
        collate_fn=collate_fn,
        prefetch_factor=prefetch_factor if num_workers > 0 else 2
        )
    class IterLoader():
        def __len__(self):
            return len(dataset)
        def __iter__(self):
            for collated_data in amassloader:
                for data in collated_data:
                    yield data
    df = td.DataFromGenerator(IterLoader())
    # df = MultiProcessRunnerZMQ(df, num_proc=num_proc)
    td.LMDBSerializer.save(df, db_loc)
    return db_loc

class AMASSdb(tudata.IterableDataset):
    def __init__(self, db_loc, transform, shuffle=False, num_workers=0, cache=None):
        self.lmdb = td.LMDBData(db_loc, shuffle=False)
        if shuffle:
            assert cache is not None, 'Sequential reads must be cached to shuffle'
            self.ds = td.LocallyShuffleData(self.lmdb, cache)
        else:
            self.ds = self.lmdb
        # data loading function
        def f(x):
            data = td.LMDBSerializer._deserialize_lmdb(x)
            return transform(data)

        if num_workers > 0:
            # unsure which of these is preferred
            # self.ds = td.MultiProcessMapDataZMQ(self.ds, num_proc=num_workers, map_func=f)
            self.ds = td.MultiThreadMapData(self.ds, num_thread=num_workers, map_func=f)
        else:
            self.ds = td.MapData(self.ds, f)

        # store number of workers
        self.num_workers = num_workers

        # reset the state and prepare an iterator
        self.ds.reset_state()
        self.ds_iter = iter(self.ds)
        self.N = self.ds.size()
        self.i = 0

    def __len__(self):
        return self.N

    def __next__(self):
        if (self.i + 1) == self.N:
            raise StopIteration
        data = next(self.ds_iter)
        self.i += 1
        return data

    def __iter__(self):
        self.i = 0
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.lmdb._close_lmdb(self)

# Cell
def amass_to_lmdb(unpacked_dir, batch_size, num_workers, overlapping=False, clip_length=1):
    amass = AMASS(
        unpacked_dir, overlapping=overlapping, clip_length=clip_length,
        transform=lambda x: x, seed=0, data_keys=('poses', 'trans')
    )
    db_loc = write_to_lmdb(amass, batch_size, num_workers)

# amass_to_lmdb('/nobackup/gngdb/repos/amass/data', 256, 8)

# Cell
def console_amass_to_lmdb():
    parser = argparse.ArgumentParser(
        description="Process AMASS into an LMDB Database for faster loading"
    )
    parser.add_argument(
        "amassloc",
        type=str,
        help="Location where AMASS has been unpacked",
    )
    parser.add_argument(
        "clip_length",
        type=int,
        help="Length of motion subsequences to save as individual examples",
    )
    parser.add_argument(
        "num_workers",
        type=int,
        help="Number of worker processes to use when loading data, does not affect resulting LMDB",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=256,
        help="Batch size used to load examples from the numpy archives, does not affect resulting LMDB",
    )
    parser.add_argument(
        "--overlapping",
        action="store_true",
        help="Whether motion subsequences should overlap, may increase LMDB size massively",
    )
    args = parser.parse_args()
    print(args)
    amass_to_lmdb(
        args.amassloc,
        args.batch_size,
        args.num_workers,
        overlapping=args.overlapping,
        clip_length=args.clip_length
    )