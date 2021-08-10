# llamass
> A Light Loader for the [AMASS dataset][amass] to make downloading and training on it easier.


To do:

* ~~Note here about the dataset license~~
* ~~Instructions on how to download the dataset~~
* Instructions on how to install the requirements for visualization
* Augmentations pulled from original AMASS repo
* ~~Install nbqa and black, run on existing notebooks~~
* Example train/test splits by unpacking different datasets to different locations
* Add CC licensed picture of llamas to github preview
* add to pypi

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
fast_amass_unpack -n 4 <.tar.bz2 directory> <directory to save unpacked data>
```

This will unpack the data in parallel in 4 jobs and provides a progress bar.

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
amass[0]
```




    {'poses': tensor([[ 8.8278e-01,  9.1215e-01,  1.4123e+00, -7.6931e-01, -1.7432e-01,
               1.4412e-01, -8.8708e-01,  1.2578e-01, -1.1743e-01,  6.2168e-01,
              -3.0015e-02, -5.0349e-02,  1.2079e+00, -5.5397e-02, -2.9298e-01,
               1.3664e+00, -4.8525e-02,  9.4145e-02, -1.2289e-01, -1.7571e-03,
               2.2975e-02, -4.0428e-02,  1.7674e-02,  7.5107e-03,  2.2632e-01,
              -5.2651e-02,  1.2855e-01, -2.5180e-02, -2.4160e-02, -2.0444e-02,
               0.0000e+00,  0.0000e+00,  0.0000e+00,  0.0000e+00,  0.0000e+00,
               0.0000e+00, -2.9401e-02, -1.1034e-01,  1.4105e-02, -5.7415e-03,
              -2.5916e-01, -6.3831e-01, -8.2118e-02,  3.6791e-01,  4.3686e-01,
               3.3646e-01,  4.1084e-02,  5.4173e-02,  3.0905e-01, -2.4670e-01,
              -7.1902e-01,  1.2193e-01,  4.5621e-01,  3.2485e-01,  2.3960e-01,
              -1.6219e+00,  4.4240e-01,  2.7042e-01,  1.7819e+00, -5.1572e-01,
              -1.2912e-02, -1.2738e-01,  3.7089e-01,  1.1892e-01, -7.0561e-02,
               6.9949e-02,  2.9811e-01, -1.5940e-01,  7.2650e-02, -1.2700e-01,
              -4.6106e-02, -1.3061e-01, -4.6657e-02, -1.3755e-02, -1.9340e-01,
              -1.8488e-01,  2.1123e-01, -1.1649e-01, -1.5284e-01,  7.5247e-02,
              -1.0174e+00,  2.7336e-02, -1.3719e-01, -1.9953e-01, -6.0931e-01,
               1.7453e-01, -5.2527e-01,  1.9633e-01, -1.5435e-02, -5.0789e-01,
              -5.9722e-01, -3.0975e-02,  8.8964e-02, -2.4794e-01,  1.6460e-01,
              -5.9515e-01, -1.7807e-01,  4.5450e-02, -4.0581e-01, -1.6256e-01,
              -2.1566e-01, -2.6343e-01,  1.4715e+00,  3.3034e-01, -4.4416e-01,
              -7.1300e-01, -4.1882e-01,  3.7449e-01,  6.2814e-01,  7.9259e-02,
              -4.0158e-01,  1.3215e-01, -7.3160e-02,  7.5620e-01,  2.5732e-01,
               1.1187e-01,  6.6922e-01, -2.0742e-01,  1.5713e-01, -6.6628e-02,
              -2.0170e-01, -2.5842e-02,  8.0069e-01, -1.2071e-01, -1.2434e-01,
               9.0385e-01,  5.5542e-02,  2.0036e-01,  4.2557e-01, -6.8690e-01,
              -8.5928e-02,  3.8910e-01,  8.3299e-01, -2.6452e-01,  1.1903e-01,
              -6.2685e-01, -2.1657e-01, -3.2647e-01, -2.1732e-01,  6.6137e-02,
               5.8971e-01, -3.1604e-01,  3.0754e-02,  8.7229e-01, -1.8293e-01,
               1.7172e-01,  4.3822e-01,  1.1091e+00, -6.0599e-01,  1.7735e-01,
              -6.4371e-01,  1.1003e-01, -3.3680e-01,  3.1729e-01,  5.0325e-01,
               9.6051e-02]]),
     'dmpls': tensor([[ 0.5872, -0.5937,  0.0935, -0.1082,  1.5400, -0.3119, -2.0400,  0.9013]]),
     'trans': tensor([[-0.1988,  0.1371,  0.6797]]),
     'betas': tensor([[ 2.2140,  2.0062,  1.7169, -1.6117,  0.5180,  1.4124, -0.1580, -0.1450,
               0.0671,  1.9010,  0.2068,  0.5701, -0.0117, -0.1653,  0.6465,  0.2017]]),
     'gender': tensor([-1])}



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


## Future Work

Caching the dataset may be easy to implement with [joblib's Memory][memory] so I'm looking into this.

[memory]: https://joblib.readthedocs.io/en/latest/generated/joblib.Memory.html
