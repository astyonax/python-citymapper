# Citymapper API in python

Python wrapper based on `requests`
of the citymapper API.

To obtain a developper key, head to the citymapper page.

## Examples
```python
>>> CM = cm.citymapper(key)
>>> CM.transit([51.525246,0.084672],[51.559098,0.074503])
{u'travel_time_minutes': 42}
>>> CM.transit([51.525246,0.084672],[51.559098,0.074503],time = '2014-11-06T19:00:02-0500',time_type='arrival')
{u'travel_time_minutes': 42}
```

## TODOs
1. test errors
2. convert times
3. implement coverage 
