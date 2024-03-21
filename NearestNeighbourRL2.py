import re
from gurobipy import *
import numpy as np

def read_file(filename):
    with open(filename, 'r') as file:
        content = file.read()  # Open the file in read mode

    data = {}  # Initialize data as an empty dictionary

    # Each file has number of inputs under which data is stored as a matrix
    numerical_data = re.findall(r'\[([\d\s.]+)\]', content)  # Extract values following each header as numerical values and remove '\t's and '\n's

    sections = ['Orders', 'Allocations', 'DistanceShelfShelf', 'DistancePackagingShelf']

    for i, section in enumerate(sections):
        data[section] = []
        lines = numerical_data[i].strip().split('\n')
        for line in lines:
            values = line.strip().split()  # Split using spaces
            data[section].append([int(val) for val in values])  # Assuming all values are integers

    return data

filename = r"Data_Xpress.txt"
data = read_file(filename)

# Extracting data into arrays
Orders = data.get('Orders')
Allocations = data.get('Allocations')
DistanceShelfShelf = data.get('DistanceShelfShelf')
DistancePackagingShelf = data.get('DistancePackagingShelf')

NbShelves = 96
Shelves = range(1, NbShelves + 1)  

DistanceShelfShelf = np.array(DistanceShelfShelf)
DistancePackagingShelf = np.array(DistancePackagingShelf)



FullDistanceMatrix = np.zeros((NbShelves+1, NbShelves+1))
for i in Shelves:
    FullDistanceMatrix[0][i] = DistancePackagingShelf[0][i-1]
    FullDistanceMatrix[i][0] = DistancePackagingShelf[0][i-1]
FullDistanceMatrix[0][0] == 0
for i in Shelves:
    for j in Shelves:
        FullDistanceMatrix[i][j] = DistanceShelfShelf[i-1][j-1]


#We have a matrix of shelves with products on them, and a matrix of orders of products. Given an order, the shelves we have to visit are the ones that have the products of the order. We want to use the nearest neighbor algorithm to find the optimal route to visit all the shelves of an order.

def find_closest_product(current_position, products, distances):
    closest_product = None
    min_distance = float('inf')
    for product in products:
        if distances[current_position][product] < min_distance:
            closest_product = product
            min_distance = distances[current_position][product]
    return closest_product

def visit_order(order, distances):
    visited = [0]
    current_position = 0  
    for k in range(len(order)):
            closest_product = find_closest_product(current_position, order, distances)
            visited.append(closest_product)                                                    #Need to fix this to ignore 0 products
            order.remove(closest_product)
            current_position = closest_product
    
    visited.append(0)
    return visited

distances = FullDistanceMatrix

TotalDistance = 0
for i, order in enumerate(Orders):

    visited_order = visit_order(order, distances)
    print(f"Order {i+1}:", visited_order)

    for i in range(len(visited_order)-1):

        TotalDistance += distances[visited_order[i]][visited_order[i+1]]

print(f"Total distance: {3*TotalDistance}")