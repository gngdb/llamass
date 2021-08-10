# llamass
> A Light Loader for the [AMASS dataset][amass] to make downloading and training on it easier.


To do:

* A way to store where the dataset has been unpacked so it can be accessed from anywhere later (probably as to append to bashrc, and backup old bashrc first)
* Note here about the dataset license
* Instructions on how to download the dataset
* Instructions on how to install the requirements (write while installing requirements)
* Augmentations pulled from original AMASS repo
* Install nbqa and black, run on existing notebooks
* Deal with train/test splits by unpacking to different locations
* Add CC licensed picture of llamas to github preview

## Install

REWRITE THIS MOST IS NOT REQUIRED

Dependencies and their associated license requirements:

* [Human Body Prior][hbp], licensed under the [SMPL-X project][smplx]

Not required:

* The [AMASS repository][amassrepo], licensed under the [AMASS project][amass]
* [Pytables][]

These have their own `requirements.txt`, often without version numbers and including unnecessary packages, making installation brittle and hostile to continuous integration. I have done my best to provide a single install procedure that should work with all of these but I can't guarantee anything. I have pinned repository installations to specific versions of each repository to try to keep it stable.

### License Agreement

Before using the AMASS dataset you're expected to sign up to the license agreeement [here][amass].

### Requirements Before Install

For [MPI's mesh library][mesh], `libboost-dev` is required:

```
sudo apt-get install libboost-dev
```



### Install with pip

To do: note here about how to install pytorch if you want to have cuda, otherwise the next step will install the regular version.

`pip install your_project_name`

### For Visualization

For visualization in notebooks it's also necessary to install:

* [Body Visualizer][body], licensed under the [SMPL-X project][smplx]
* MAYBE [mesh][], does not require a sign up page

**To do**: provide script to install this and all its requirements.



[amassrepo]: https://github.com/nghorbani/amass/blob/master/notebooks/01-AMASS_Visualization.ipynb
[body]: https://github.com/nghorbani/body_visualizer
[smplx]: https://smpl-x.is.tue.mpg.de/
[mesh]: https://github.com/MPI-IS/mesh
[amass]: https://amass.is.tue.mpg.de/index.html
[pytables]: https://www.pytables.org/index.html

## How to use

To do: explain these steps

Steps:

1. Unpack the dataset
2. Maybe not: Prepare the dataset
3. Use the PyTorch Dataset in a DataLoader

## Future Work

Caching
