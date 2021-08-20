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
first to install it with cuda.

`pip install llamass`

### For Visualization

**To do**: provide script to install this and all its requirements (for curl into bash on colab would be nice)

* [Human Body Prior][hbp], licensed under the [SMPL-X project][smplx]
* [Body Visualizer][body], licensed under the [SMPL-X project][smplx]
* MAYBE [mesh][], does not require a sign up page

For [MPI's mesh library][mesh], `libboost-dev` is required:

```
sudo apt-get install libboost-dev
```

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

    sample_data/sample.tar.bz2 extracting to /tmp/tmp2mpzo7r2


### Using the data

Once the data is unpacked it can be loaded by a PyTorch DataLoader directly using the `llamass.core.AMASS` Dataset class.

* `overlapping`: whether the clips of frames taken from each file should be allowed to overlap
* `clip_length`: how long should clips from each file be?
* `transform`: a transformation function apply to all fields

```python
import torch
from torch.utils.data import DataLoader

amass = llamass.core.AMASS(
    unpacked_directory, overlapping=False, clip_length=1, transform=torch.tensor
)
```

```python
amassloader = DataLoader(amass, batch_size=4, shuffle=True)

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

* Add step in setup above to wget the file lengths
* Instructions on how to install the requirements for visualization
* Augmentations pulled from original AMASS repo
* Example train/test splits by unpacking different datasets to different locations
