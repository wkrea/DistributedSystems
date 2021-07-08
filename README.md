# Distributed Systems

Solutions for the practical assignments of the Distributed Systems course at the University of Antwerp, 2018-2019 acadamic year. For this project we had to make a number of assignments using RESTful API's, Docker microservices, and Apache Spark. Please note that the solutions are in Dutch instead of English. Furthermore, the solutions may no longer work due to changes in the API of De Lijn.

## Files
 - ```opdracht1_DeLijnRealtime```
    - ```manual.pdf```: usage of the application, as well as the API
    - ```code```: the web application itself
 - ```opdracht2_Reviews```
    - ```opdracht2_manual.pdf```: usage of the application, as well as the API
    - ```code```: the code for the docker microservices
 - ```opdracht3_SparkMapReduce```
    - ```preprocessing```: preprocessing code and information
    - the notebooks that contain the solutions
    - data files
 - ```assignments```: the original assignment descriptions

## Assignment 1

For this assignment we had to connect to the API of the Flemish public transportation service (De Lijn) and retrieve informations about the different vehicles, stops, and routes. We had to combine this information with a weather API to obtain the weather situation at each stop. This information was then presented to the user in a web interface. On a map the user can see the different vehicles and stops on a map. If the user clicks on a stop, weather information will be visible.

## Assignment 2

We had to make an application based on microservices that allowed to user to place reviews for the different stops and vehicles of De Lijn.

## Assignment 3

In the final assignment, we had to collect information from the API of De Lijn and then aggregate it using Apache Spark. The solutions were presented in Jupyter notebooks.

