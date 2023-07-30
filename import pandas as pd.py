import pandas as pd
import folium
import webbrowser
from haversine import haversine
import networkx as nx
from itertools import combinations

# Load the dataset from the provided CSV file
data = pd.read_csv('C:\\Users\\Omkar\\Downloads\\Book1.csv')

# Function to calculate the distance between two GPS coordinates using the haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    return haversine((lat1, lon1), (lat2, lon2))

# Coordinates for the company location (replace with your actual coordinates)
company_latitude = 29.6385821320874
company_longitude = -98.08809980926696

# Calculate distances to company and create bus stops for employees within 10 km of the company
data['distance_to_company'] = data.apply(lambda row: calculate_distance(row['latitude'], row['longitude'], company_latitude, company_longitude), axis=1)
bus_stops = data[data['distance_to_company'] <= 10].copy()

# Create a DataFrame to keep track of bus stop assignments for each employee
bus_stop_assignments = pd.DataFrame(columns=['latitude', 'longitude'])

# Create a list to keep track of the assigned stops for each employee
employee_assigned_stops = []

# Iterate through each employee and assign them to a bus stop
for index, row in data.iterrows():
    assigned_stops = []
    for stop_index, stop_row in bus_stops.iterrows():
        if calculate_distance(row['latitude'], row['longitude'], stop_row['latitude'], stop_row['longitude']) <= 10:
            assigned_stop = stop_row[['latitude', 'longitude']].copy()
            assigned_stops.append(assigned_stop)
    if not assigned_stops:
        # If no bus stop is found within 10 km, create a new bus stop for the employee
        assigned_stop = pd.DataFrame({'latitude': row['latitude'], 'longitude': row['longitude']}, index=[0])
        bus_stops = pd.concat([bus_stops, assigned_stop], ignore_index=True)
        assigned_stops.append(assigned_stop)

    employee_assigned_stops.append(assigned_stops)

# Create a map
map_center = [data['latitude'].mean(), data['longitude'].mean()]
mymap = folium.Map(location=map_center, zoom_start=10)

# Add markers for each bus stop
for index, row in bus_stops.iterrows():
    num_employees = len(employee_assigned_stops[index])
    num_buses = (num_employees - 1) // 70 + 1
    popup_text = f"Bus Stop {index + 1}\nNumber of Employees: {num_employees}\nNumber of Buses: {num_buses}"
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=popup_text,
        icon=folium.Icon(color='green')
    ).add_to(mymap)

# Add a marker for the company
folium.Marker(
    location=[company_latitude, company_longitude],
    popup='Company',
    icon=folium.Icon(color='red')
).add_to(mymap)

# Create a graph for bus stops and the company
G = nx.Graph()

# Add nodes for bus stops
for index, row in bus_stops.iterrows():
    G.add_node(index, pos=(row['latitude'], row['longitude']))

# Add node for the company
G.add_node('Company', pos=(company_latitude, company_longitude))

# Calculate distances between bus stops and the company and add edges to the graph
for i, j in combinations(bus_stops.index.tolist() + ['Company'], 2):
    if i != j:
        distance = calculate_distance(*G.nodes[i]['pos'], *G.nodes[j]['pos'])
        G.add_edge(i, j, weight=distance)

# Calculate shortest paths using Dijkstra's algorithm and find the routes for each employee
bus_capacity = 70
route_stops = []
for employee_stops in employee_assigned_stops:
    current_stop = 'Company'
    route = []
    for stop in employee_stops:
        source = current_stop
        target = bus_stops.loc[(bus_stops['latitude'] == stop['latitude']) & (bus_stops['longitude'] == stop['longitude'])].index[0]
        shortest_path = nx.shortest_path(G, source=source, target=target, weight='weight')
        route.extend(shortest_path[1:])
        current_stop = target
    route_stops.append(route)

# Color the routes on the map
route_colors = ['blue', 'green', 'red', 'orange', 'purple']  # Use different colors for each route
for i, route in enumerate(route_stops):
    route_coordinates = [(bus_stops.loc[stop, 'latitude'], bus_stops.loc[stop, 'longitude']) for stop in route]
    folium.PolyLine(locations=route_coordinates, color=route_colors[i % len(route_colors)]).add_to(mymap)

# Save the map to an HTML file
map_file = 'bus_stops_map.html'
mymap.save(map_file)

# Open the map in the browser
webbrowser.open(map_file)
