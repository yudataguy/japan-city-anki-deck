# Import modules
import requests
import numpy as np
import pandas as pd

# Load csv city file
city = pd.read_csv('city_eng.csv', index_col=False)

# Add a nation column, for better research result
city['country'] = 'japan'
city['prefecture'] = city['prefecture'].replace('Hyōgo', 'Hyogo', regex=True) 
city['combo'] = city['city'] + '+' + city['prefecture'] + '+' + city['country']
city['combo'] = city['combo'].replace(' ', '+', regex=True)
city['combo'] = city['combo'].replace('-', '+', regex=True)
city['image'] = city['combo'] + '.png'

# Enter your api key here
api_key = "YOUR_API_KEY"
 
# base url for google map static image
url = "https://maps.googleapis.com/maps/api/staticmap?key="
 
# center defines the center of the map
centers = city['combo'].tolist()
# Zoom level of the map
zoom = 12

option = "&format=png&maptype=roadmap&style=feature:administrative.locality%7Celement:labels.text%7Cvisibility:off&style=feature:administrative.neighborhood%7Celement:geometry.fill%7Ccolor:0xff5848&style=feature:landscape.man_made%7Cvisibility:off&style=feature:poi%7Cvisibility:on&style=feature:poi.business%7Cvisibility:off&style=feature:poi.government%7Cvisibility:off&style=feature:poi.school%7Cvisibility:off&style=feature:road%7Celement:labels.icon%7Cvisibility:off&style=feature:road.arterial%7Cvisibility:off&style=feature:road.highway%7Celement:labels%7Cvisibility:off&style=feature:road.local%7Cvisibility:off&style=feature:transit%7Cvisibility:off&style=feature:transit.line%7Celement:geometry.fill%7Cvisibility:on&style=feature:transit.line%7Celement:labels.text%7Cvisibility:on&style=feature:transit.station.airport%7Cvisibility:on%7Cweight:1&style=feature:transit.station.airport%7Celement:geometry.fill%7Cvisibility:on&style=feature:transit.station.rail%7Cvisibility:on&style=feature:transit.station.rail%7Celement:geometry.fill%7Cvisibility:simplified&size=480x360&scale=2" 

# Request and save map image
for center in centers:
    # Create request url
    r = requests.get(url + api_key + "&center=" + center + "&zoom=" + str(zoom) + option)
    # Save it as image
    img_name = 'map/' + center + '.png'
    f = open(img_name,'wb')
    # Write the content
    f.write(r.content)
    # Close the file
    f.close()

# Create a complete dataframe to combine japanese and english
jp_city_final = city
jp_city_final = jp_city_final.drop(columns=['combo', 'country'])
jp_city_final['population'] = jp_city_final['population'].replace(',', '', regex=True)
jp_city_final['population'] = jp_city_final['population'].astype(int)
jp_city_final['html'] = '<img src="' + jp_city_final['image'] + '">'


# Get basic statistics from the population
jp_city_final['population'].describe()

# Import Japanese city name
japanese = pd.read_excel('jp_cities_wiki_0.xlsx')
# Combine Japanese and English columns
jp_city_final = pd.concat([japanese, jp_city_final], axis=1)
# Make prefecture as tag for anki
jp_city_final['tag'] = jp_city_final['prefecture']
# Drop image col
jp_city_final = jp_city_final.drop(columns=['image'])

# Save dataframe to csv file 
jp_city_final.to_csv('jp_city_final.csv', encoding='utf-8', index=False)