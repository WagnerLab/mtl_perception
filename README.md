## When the ventral visual stream is not enough: A deep learning account of medial temporal lobe involvement in perception

To create the python environment used to generate and analyze all data in the current repository, install conda (v4.8.5, tested on an osx-64 platform) and run the following command in the current directory:

```
$ conda env create -f conda_environment.yml
```

We use python 3.7.5. The structure of this repository reflects the main findings detailed in the manuscript `summary/manuscript/preprint.pdf`. A brief discription of the folder/analysis structure: 

- `electrophysiological/`: fit models to electrophysiological recordings from the VVS and identify IT-like layer  
- `retrospective/`: generate model performance on all experiments in the  retrospective dataset
- `high-throughput/`: collect human behavior online on  novel dataset and preprocess the results 
- `in_silico/`: examine effects of changing model architecture and trained data on PRC-relevant behavior 

Each of these folders contains results as well as the functions used to generate them. For example, running `electrophysiological/automate_layer_fits.py` on a cluster parallelizes `layer_neural_fit.py` to generate all results contained in `electrophysiological/pls_fitting_results/`. Running these analyses on a desktop computer is infeasible. These results across folders are compiled in  


- `summary/`: reporting statistical effects, generating figures, and final manuscript 


Summary statistics and figures used in the manuscript can be generated by opening the jupyter notebook `summary/reporting_statistics.ipynb` and setting the kernal to the conda environment `mtl_perception`. This notebook calls custom functions and integrates results already located within other folders (e.g. `electrophysiological/reliability_and_fitting_results.pickle`). Because the results from previous analyses are imported into this summary notebook, there are no expected latencies. 

Generating the result files in each directory would require the electrophysiological data and stimuli used for the modeling work, as well as cluster-based computational resources; these files are not included, but can be provided upon request. 

Questions or comments? Feel free to contact me at tyler [ dot ] ray [ dot ] bonnen [ at ] gmail [ dot ] com 
