# llamass
> A Light Loader for the [AMASS dataset][amass] to make downloading and training on it easier.


## Badges

[![PyPI version](https://badge.fury.io/py/llamass.svg)](https://badge.fury.io/py/llamass)


![example workflow](https://github.com/gngdb/llamass/workflows/CI/badge.svg)


## Install

### License Agreement

Before using the AMASS dataset I'm expected to sign up to the license agreeement [here][amass]. This package doesn't require any other code from MPI but visualization of pose data does, see below.

### Install with pip

Requirements are handled by pip during the install but in a new environment I would install [pytorch][]
first to configure cuda as required for the system.

`pip install llamass`

### For Visualization

To visualise this data [MPI][] packages are required and they ask you to sign up to abide by their license:

* [Human Body Prior][hbp], licensed under the [SMPL-X project][smplx]
* [Body Visualizer][body], licensed under the [SMPL-X project][smplx]

To install on e.g. colab the following code snippet should work (I've fixed versions because these are the versions I've tested):

```
import os
os.environ["PYOPENGL_PLATFORM"] = "egl"
!pip install pyrender
!pip install mediapy
!pip install human_body_prior@git+https://github.com/nghorbani/human_body_prior@7f0a4b3#egg=human_body_prior
!pip install body_visualizer@git+https://github.com/nghorbani/body_visualizer@fe4e5e8#egg=body_visualizer
```

This relies on EGL being installed, which it is on colab but may require some configuration 

[mpi]: https://is.mpg.de/
[hbp]: https://github.com/nghorbani/human_body_prior
[pytorch]: https://pytorch.org/get-started/locally/
[amassrepo]: https://github.com/nghorbani/amass/blob/master/notebooks/01-AMASS_Visualization.ipynb
[body]: https://github.com/nghorbani/body_visualizer
[smplx]: https://smpl-x.is.tue.mpg.de/
[mesh]: https://github.com/MPI-IS/mesh
[amass]: https://amass.is.tue.mpg.de/index.html
[pytables]: https://www.pytables.org/index.html

## How to use

### Downloading the data

The [AMASS website][amass] provides links to download the various parts of the AMASS dataset. Each is provided as a `.tar.bz2` and I had to download them from the website by hand. Save all of these in a folder somehwere.

### Unpacking the data

After installing `llamass` a console script is provided to unpack the `tar.bz2` files downloaded from the [AMASS][] website:

```
fast_amass_unpack -n 4 --verify <dir with .tar.bz2 files> <dir to save unpacked data>
```

This will unpack the data in parallel in 4 jobs and provides a progress bar. The `--verify` flag will `md5sum` the directory the files are unpacked to and check it against what I found when I unpacked it. It'll also avoid unpacking tar files that have already been unpacked by looking for saved `.hash` files in the target directory. It's slower but more reliable and recovers from incomplete unpacking.

Alternatively, this can be access in the library using the `llamass.core.unpack_body_models` function:

[amass]: https://amass.is.tue.mpg.de/index.html

```python
import llamass.core

llamass.core.unpack_body_models("sample_data/", unpacked_directory, 4)
```

    sample_data/sample.tar.bz2 extracting to /tmp/tmpgwqr1443


### Download Metadata

I've processed the files to find out how many frames are in each numpy archive unpacked when `fast_amass_unpack` is run. By default, the first time the `AMASS` Dataset object is asked for it's `len` it will look for a file containing this information in the specified AMASS directory. If it doesn't find it, it will recompute it and that can take 5 minutes.

Save 5 minutes by downloading it from this repository:

```
wget https://github.com/gngdb/llamass/raw/master/npz_file_lens.json.gz -P <dir to save unpacked data>
```

### Using the data

Once the data is unpacked it can be loaded by a PyTorch DataLoader directly using the `llamass.core.AMASS` Dataset class.

* `overlapping`: whether the clips of frames taken from each file should be allowed to overlap
* `clip_length`: how long should clips from each file be?
* `transform`: a transformation function apply to all fields

It is an [IterableDataset][] so it **cannot be shuffled by the DataLoader**. If `shuffle=True` the DataLoader will hit an error. However, the `AMASS` class itself implements shuffling and it can be enabled using `shuffle=True` at initialisation.

[iterabledataset]: https://pytorch.org/docs/stable/data.html#iterable-style-datasets

```python
import torch
from torch.utils.data import DataLoader

amass = llamass.core.AMASS(
    unpacked_directory,
    overlapping=False,
    clip_length=1,
    transform=torch.tensor,
    shuffle=True,
    seed=0,
)
```

```python
amassloader = DataLoader(amass, batch_size=4)

for data in amassloader:
    for k in data:
        print(k, data[k].size())
    break
```

    poses torch.Size([4, 1, 156])
    dmpls torch.Size([4, 1, 8])
    trans torch.Size([4, 1, 3])
    betas torch.Size([4, 1, 16])
    gender torch.Size([4, 1])


## To do

To do:

* ~~Add step in setup above to wget the file lengths~~
* ~~Instructions on how to install the requirements for visualization~~
* Augmentations pulled from original AMASS repo
* Example train/test splits by unpacking different datasets to different locations
* Update and link the colab notebook demonstrating visualization
