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

filename = r"C:\Users\s2026970\Downloads\TestSet.txt"
data = read_file(filename)

# Extracting data into arrays
Orders = data.get('Orders')
Allocations = data.get('Allocations')
DistanceShelfShelf = data.get('DistanceShelfShelf')
DistancePackagingShelf = data.get('DistancePackagingShelf')


Allocation = Allocations[0]

NbOrders = len(Orders)
OrderSize = 5
NbProductGroups = 90
NbShelves = 96



ProductGroups = range(1, NbProductGroups + 1)
Orders_ = range(1, NbOrders + 1)
Shelves = range(1, NbShelves + 1)  
ShelvesDoor = range(NbShelves+1)



OrderMatrix = np.array(Orders)

DistanceShelfShelf = np.array(DistanceShelfShelf)
DistancePackagingShelf = np.array(DistancePackagingShelf)



FullDistanceMatrix = np.zeros((NbShelves+1, NbShelves+1))
for i in Shelves:
    FullDistanceMatrix[0][i] = DistancePackagingShelf[0][i-1]
    FullDistanceMatrix[i][0] = DistancePackagingShelf[0][i-1]
FullDistanceMatrix[0][0] = 0
for i in Shelves:
    for j in Shelves:
        FullDistanceMatrix[i][j] = DistanceShelfShelf[i-1][j-1]




FullOrderMatrix = np.zeros((NbOrders + 1, NbProductGroups + 1))
for k in range(NbOrders):
    for p in range(OrderSize):
        if OrderMatrix[k][p] != 0:
            FullOrderMatrix[k][OrderMatrix[k][p]] = 1




NbProductsPerOrder = np.zeros(NbOrders)
for k in range(NbOrders):
    NbProductsPerOrder[k] = sum(FullOrderMatrix[k][p] for p in ProductGroups)



#Initialise Model
m = Model("WAP")


#Decision Variables
x = m.addVars(ShelvesDoor, ProductGroups, vtype=GRB.BINARY, name = 'x')
y = m.addVars(ShelvesDoor, ShelvesDoor, Orders_, vtype=GRB.BINARY, name = 'y')
u = m.addVars(ShelvesDoor, Orders_, lb = 1, ub = 5,  vtype = GRB.CONTINUOUS, name = 'u')
z = m.addVars(ShelvesDoor, Orders_, vtype=GRB.BINARY, name = 'z')

#Optimization Type
m.ModelSense = GRB.MINIMIZE

#Objective Function
m.setObjective(3*quicksum(FullDistanceMatrix[i][j]*y[i,j,k] for k in Orders_ for i in ShelvesDoor for j in ShelvesDoor))

#Constraints

'''for p in ProductGroups:
    x[0, p] = 0'''

for i in ShelvesDoor:
    if Allocation[i-1] != 0:
        for p in ProductGroups:

            x[0, p] = 0

            if p == Allocation[i]:
                x[i, p] = 1
            else:
                x[i, p] = 0


#Can't go from shelf i to shelf i
m.addConstrs((y[i,i,k] == 0 for i in ShelvesDoor for k in Orders_), name = 'NoSelfLoop')

#Each shelf should not be visited more than once per route:
#m.addConstrs((quicksum(y[i,j,k] for j in ShelvesDoor) <= 1 for i in ShelvesDoor for k in Orders_), name = 'EnterShelfOnce')
m.addConstrs((quicksum(y[i,j,k] for i in ShelvesDoor) <= 1 for j in ShelvesDoor for k in Orders_), name = 'LeaveShelfOnce')

m.addConstrs((quicksum(y[i,j,k] for i in ShelvesDoor) == quicksum(y[j,i,k] for j in ShelvesDoor) for k in Orders_), name = 'LeaveShelfOnce')

#Only visit shelves that correspond to the products in the order
m.addConstrs((quicksum(y[i,j,k] for i in Shelves) == x[j,p] for j in ShelvesDoor for k in Orders_ for p in ProductGroups), name = 'Assign')

#MTZ constraints
m.addConstrs((u[i, k] - u[j, k] + NbProductsPerOrder[k-1] * y[i, j, k] <= NbProductsPerOrder[k-1]-1 for i in ShelvesDoor for j in ShelvesDoor for k in Orders_), name = 'Track position')

#Each route must begin at the door
m.addConstrs((quicksum(y[0, j, k] for j in ShelvesDoor) == 1 for k in Orders_), name = 'StartAtDoor')

#Each route must end at the door
m.addConstrs((quicksum(y[i, 0, k] for i in ShelvesDoor) == 1 for k in Orders_), name = 'EndAtDoor')



m.Params.TimeLimit = 1
m.update()

try:
    m.optimize()
    print("Optimization complete.")
except KeyboardInterrupt:
    print("Keyboard interrupt detected. Terminating optimization.")
    m.terminate()

if m.status == GRB.INFEASIBLE:
        m.computeIIS()
        m.write("infeasible.lp")
        print('\nThe following constraint(s) cannot be satisfied:')
        for c in m.getConstrs():
            if c.IISConstr:
                print('%s' % c.constrName)

if m.Status == GRB.OPTIMAL:
    keys_greater_than_zero = [key for key, var in y.items() if var.X > 0.0]
    print(keys_greater_than_zero)