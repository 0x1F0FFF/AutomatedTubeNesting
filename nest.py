#! /usr/bin/env python3

"""
    Project:    Nest
    Version:    4.0
    Author:     Morten
"""

import argparse
import pandas as pd
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(1, '~/.source/or-tools')
from ortools.linear_solver import pywraplp

global debug
debug = False

def visualizer(data, nests):
    """
    Creates new dataframe for visualization. Columns are all tube IDs
    and row index is particular tube nest (note that I said nest not nests).
    It then adds length value for tube ID only if it is in that particular nest.
    """
    visualising_data = pd.DataFrame(columns=[list(range(len(data["names"])))], index=[list(range(len(nests)))])
    visualising_data = visualising_data.fillna(0)
    tube = 0
    for nest in nests:
        for part in nest:
            visualising_data.loc[tube, part] = int(data["lengths"][part])
            
        tube += 1

    """
    For the graph we then change the column names from part ID to part names.
    Then we add +1 to every nest number / nest ID so our graph starts from one.
    We finally combine the columns with the same part name.
    """
    visualising_data.columns = data["names"]
    visualising_data.index = [element + 1 for element in list(range(len(nests)))]
    visualising_data = visualising_data.groupby(level=0, axis=1).sum()
    ax = visualising_data.plot.barh(stacked=True, figsize=(10, 5))
    plt.xlabel("Length used")
    plt.ylabel("Tube #")
    plt.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))

    for c in ax.containers:
        labels = [f'{w:.0f}' if (w := v.get_width()) > 0 else '' for v in c]
        ax.bar_label(c, labels=labels, label_type="center")
    
    #plt.savefig('solution.png')
    plt.show()
    return visualising_data

def cost(data, dataframe, nests, tube_length):
    # Total length of used tubes in mm
    number_of_tubes_used = list(range(len(nests)))
    total_tubes_length = (int(number_of_tubes_used[-1])+1) * (tube_length+130)

    # Total part lengths in mm
    dataframe.loc["Total"] = dataframe.sum()
    dataframe["Total"] = dataframe.sum(axis=1)
    total_parts_length = dataframe.loc["Total"]["Total"]

    for part in data.index:
        cost_of_material = (total_tubes_length * data["Length"][part]) / total_parts_length
        print ("Part: " + str(data["Part"][part]) + " Cost of material: " + str(cost_of_material) + " Part length: " + str(data["Length"][part]))
            
def solver(data):
    """
    Black magic.
    """
    nests = []
    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver('SCIP')

    # Variables
    # x[i, j] = 1 if tube i is nested in tube j.
    x = {}
    for i in data['parts']:
        for j in data['tubes']:
            x[(i, j)] = solver.IntVar(0, 1, 'x_%i_%i' % (i, j))

    # y[j] = 1 if tube j is used.
    y = {}
    for j in data['tubes']:
        y[j] = solver.IntVar(0, 1, 'y[%i]' % j)

    # Constraints
    # Each part must be in exactly one tube since we created new IDs
    # every part, even with the same name parts.
    for i in data['parts']:
        solver.Add(sum(x[i, j] for j in data['tubes']) == 1)

    # The amount packed in each tube cannot exceed its capacity.
    for j in data['tubes']:
        solver.Add(sum(x[(i, j)] * data['lengths'][i] for i in data['parts']) <= y[j] * data['tube_length'])

    # Objective: minimize the number of tubes used.
    solver.Minimize(solver.Sum([y[j] for j in data['tubes']]))

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        num_tubes = 0.
        for j in data['tubes']:
            if y[j].solution_value() == 1:
                tube_parts  = []
                tube_length = 0
                for i in data['parts']:
                    if x[i, j].solution_value() > 0:
                        tube_parts.append(i)
                        tube_length += data['lengths'][i]
                if tube_length > 0:
                    num_tubes += 1
                    # For visualizing the nests
                    nests.insert(j, tube_parts)
        info = '[*] Time: ' + str(solver.WallTime()) + 'ms'
        log (info)
        return nests
    else:
        print('Optimal solution not found.')
        sys.exit(0)

def create_data_model(data, material_length):
    """
    Creates dictionary for solver - includes
    list of lengths, list of part names,
    list of part ID's, material length
    """
    log('[*] Creating data model.')

    dataset = {}
    lengths = []
    parts = []

    for part in data.index:
        for count in range(data['Quantity'][part]):
            lengths.append(data['Length'][part])
            parts.append(data['Part'][part])

    dataset['lengths'] = lengths
    dataset['parts'] = list(range(len(lengths)))
    dataset['tubes'] = dataset['parts']
    dataset['tube_length'] = material_length
    dataset['names'] = parts

    return dataset

def get_data(path):
    """
    Acquires tube information from excel for nesting.
    Method uses Pandas packages.
    """
    try:
        excel = pd.read_excel(path, header=[0])
        log('[+] Access to data established.')
    except:
        print ("Error reading passed Excel file.")
        log('[!] Failed to acquire data.')

    return excel

def log(msg):
    global debug
    if debug:
        print (msg)

def main():
    """
    Works with passed arguments, directs input into
    the next step.
    """
    parser = argparse.ArgumentParser(description='Tube nesting program')
    parser.add_argument('-e', '--excel', help='Argument to pass excel file')
    parser.add_argument('-m', '--material', help='Argument to pass material length')
    parser.add_argument('-d', '--debug', help='Enables debug mode', action='store_true')

    args = parser.parse_args()
    
    global debug
    if args.debug:
        log('[+] Debugging enabled.')
        debug = True
    if (args.material is not None):
        try:
            tube_length = int(args.material)
        except:
            print ('[!] Error setting material length.')
            sys.exit(0)
    if (args.material is None):
        tube_length = 5870 # default value
    if (args.excel is not None):
        log ('[*] Working with Excel spreadsheet.')
        data = get_data(args.excel) # next operation
        
    dataset = create_data_model(data, tube_length)
    nests = solver(dataset)
    dataframe = visualizer(dataset, nests)
    cost(data, dataframe, nests, tube_length)

if __name__ == '__main__':
    main()

