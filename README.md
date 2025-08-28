# CSP-based minesweeper agent
## Authors
* Alice Nicoletta
* Gaetano Barresi
* Leonardo Cozzolino

## Hot to use 
To start a run with GUI, just this snippet of code in your terminal: 
```
git clone https://github.com/tanobar/minesweeper_prj.git
cd minesweeper_prj
python main.py
```
Please be forgiving with the agent, the default grid is 16x30 with 99 bombs, a very hard game!
Values for the grid size and number of mines can be changed on line 58 of the main.py script.

To run the assessment script, run:
```
python simple_assessment.py
```
And follow the instructions.

To run the PR assessment, run:
```
python test_prob_reasoning.py
```

## Requirements
In order to pursue minimality, we decided to stick on python built-in modules.
No virtual environment, no external dependencies and no "it works on my machine" for this project.
We sacrificed performance and speed-ups in the name of simplicity and portability. 
## Features 
* GUI
* different options for the agent, for testing
