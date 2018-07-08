# Anki Deck: Japanese Cities

## Overview: 

Anki Shared Deck: 

This anki deck includes 815 Japanese cities/wards, sorted by population. The deck includes three types of card, 
1. Japanese city name / Romaji city name
2. Romaji city name / Japanese city name
3. Map

## Map Customization:

The map file is generated with [Google Map API](https://developers.google.com/maps/documentation/), with map label customization. It hides the city and prefecture text and shows the train station and attraction. Aim to improve geography knowledge.

Map label customization made with https://mapstyle.withgoogle.com/, customized JSON file included. You can either build on current customization with import JSON file on the website or build customization from scratch. 

Google Map static image URL format: 
```
https://maps.googleapis.com/maps/api/staticmap?key=YOUR_API_KEY&center=35.686929517283644,139.74463444470223&zoom=13&format=png&maptype=roadmap&style=feature:administrative.locality%7Celement:labels.text%7Cvisibility:off&style=feature:administrative.neighborhood%7Celement:geometry.fill%7Ccolor:0xff5848&style=feature:landscape.man_made%7Cvisibility:off&style=feature:poi%7Cvisibility:on&style=feature:poi.business%7Cvisibility:off&style=feature:poi.government%7Cvisibility:off&style=feature:poi.school%7Cvisibility:off&style=feature:road%7Celement:labels.icon%7Cvisibility:off&style=feature:road.arterial%7Cvisibility:off&style=feature:road.highway%7Celement:labels%7Cvisibility:off&style=feature:road.local%7Cvisibility:off&style=feature:transit%7Cvisibility:off&style=feature:transit.line%7Celement:geometry.fill%7Cvisibility:on&style=feature:transit.line%7Celement:labels.text%7Cvisibility:on&style=feature:transit.station.airport%7Cvisibility:on%7Cweight:1&style=feature:transit.station.airport%7Celement:geometry.fill%7Cvisibility:on&style=feature:transit.station.rail%7Cvisibility:on&style=feature:transit.station.rail%7Celement:geometry.fill%7Cvisibility:simplified&size=480x360&scale=2
```

Reference: Google Map API Static Maps [Developer Guide](https://developers.google.com/maps/documentation/maps-static/dev-guide)

### Zoom Level:
```
    1: World
    5: Landmass/continent
    10: City
    15: Streets
    20: Buildings
```

## Deck Field:
1. Japanese Prefecture
2. Japanese City
3. Romaji Prefecture
4. Romaji City
5. Population (Survey: April 2018)
6. Image Html Code

Reference: Japanese City Ranking by Population ([Wikipedia](https://ja.wikipedia.org/wiki/%E6%97%A5%E6%9C%AC%E3%81%AE%E5%B8%82%E3%81%AE%E4%BA%BA%E5%8F%A3%E9%A0%86%E4%BD%8D))

## Issue: 
1. Possible translation error: All translation made by Google Translate, some were fixed, some may remain. 
2. Possible inaccurate map: due to inaccurate name or translation. 

## Contribution: 
All contributions are welcome:
* Read the issues, For the project and do a Pull Request. 
* Request a new issue with creating a `New issue` with the `enhancement` tag. 
* Find any kind of errors in the deck and create a `New issue` with the details or fork the project and do a Pull Request.
* Suggest an improvement for the deck.
* Contribution (Code of Conduct)[code-of-conduct.md]

## License:

[MIT](LICENSE)

