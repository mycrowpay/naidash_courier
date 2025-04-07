import logging
import requests

from datetime import datetime, date, timedelta
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import AccessDenied, AccessError, ValidationError, UserError

logger = logging.getLogger(__name__)

class NaidashMap:    
    def forward_geocoding_using_openstreetmap(self, address):
        """
        Use Openstreetmap to retrieve location details within Kenya
        :return: location details or None if not found
        """
        
        response_data = dict()
        headers = {"Accept-Language": "en_US", "User-Agent": "Naidash"}
        
        base_url = request.env['ir.config_parameter'].sudo().get_param('naidash_courier.openstreetmap_base_url')
        url = f"{base_url}/search"        
        
        try:
            if not base_url:
                response_data["code"] = 404
                response_data["message"] = "Base URL not found"
                return response_data
            
            response = requests.get(url, headers=headers, params={"format": "json", "countrycodes": "ke", "q": address})
            location = response.json()            
            
            if location:
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = location
            else:
                response_data["code"] = 404
                response_data["message"] = "Location not found"
                
            return response_data
        except Exception as e:
            raise e
    
    def reverse_geocoding_using_openstreetmap(self, latitude, longitude):
        """
        Use Openstreetmap to retrieve details of the location address
        :return: the address details
        """
        
        response_data = dict()
        headers = {"Accept-Language": "en_US", "User-Agent": "Naidash"}
        
        base_url = request.env['ir.config_parameter'].sudo().get_param('naidash_courier.openstreetmap_base_url')
        url = f"{base_url}/reverse"
        
        try:
            if not base_url:
                response_data["code"] = 404
                response_data["message"] = "Base URL not found"
                return response_data

            response = requests.get(url, headers=headers, params={"lat": latitude, "lon": longitude, "format": "json", "namedetails": 1})
            address = response.json()
            
            if address:
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = address
            else:
                response_data["code"] = 404
                response_data["message"] = "Address not found"
                
            return response_data
        except Exception as e:
            raise e
        
    def get_optimized_directions_using_mapbox(self, coordinates, is_roundtrip="false", profile="driving-traffic"):
        """
        Use Mapbox to retrieve optimized routes with driving-traffic profile
        :return: navigation details
        """
        
        response_data = dict()
        headers = {"Accept-Language": "en_US"}
        
        base_url = request.env['ir.config_parameter'].sudo().get_param('naidash_courier.mapbox_base_url')
        mapbox_access_token = request.env['ir.config_parameter'].sudo().get_param('naidash_courier.mapbox_access_token')
        url = f"{base_url}/optimized-trips/v1/mapbox/{profile}/{coordinates}"
        
        try:
            if not base_url:
                response_data["code"] = 500
                response_data["message"] = "Setup the Base URL"
                return response_data
            
            if not mapbox_access_token:
                response_data["code"] = 500
                response_data["message"] = "Provide the access token"
                return response_data            
                        
            if not coordinates:
                response_data["code"] = 400
                response_data["message"] = "GPS coordinates are required!"
                return response_data
            
            response = requests.get(url, headers=headers, params={"access_token": mapbox_access_token, "roundtrip": is_roundtrip, "geometries": "geojson", "language": "en", "overview": "full", "steps": "true", "source": "first", "destination": "last"})
            directions = response.json()

            logger.info(f"Logging The Navigation Link: {response.url}")

            if directions:
                # Add the navigation link and in future, 
                # using an opensource URL shortener service for the direction_url
                directions["trips"][0]["directions_url"] = response.url
                
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = directions
            else:
                response_data["code"] = 404
                response_data["message"] = "Directions not found"
                
            return response_data
        except Exception as e:
            raise e