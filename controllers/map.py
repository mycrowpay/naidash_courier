# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request, route, SessionExpiredException
from odoo.service import security
from odoo.service.security import check_session
from ..models.map import NaidashMap

logger = logging.getLogger(__name__)
naimap = NaidashMap()

class NaidashMap(http.Controller):
    @route('/api/v1/map/search', methods=['GET'], auth='user', type='http')
    def get_location_details(self):
        """Get the location details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:           
            search_address = request.params.get('address')
            latitude = request.params.get('latitude')
            longitude = request.params.get('longitude')
            status_code = 400            
            
            data = json.dumps(
                {
                    "error": {
                        "code": status_code,
                        "message": "Either search address or latitude and longitude are required!"
                    }
                }
            )
            
            if search_address and (not latitude or not longitude):            
                location_details = naimap.forward_geocoding_using_openstreetmap(search_address)
                status_code = location_details.get("code")
                
                if status_code == 404:
                    data = json.dumps(
                        {
                            "error": location_details
                        }
                    )

                else:
                    data = json.dumps(
                        {
                            "result": location_details
                        }
                    )

            elif (latitude and longitude) and not search_address:
                address_details = naimap.reverse_geocoding_using_openstreetmap(latitude, longitude)
                status_code = address_details.get("code")
                
                if status_code == 404:
                    data = json.dumps(
                        {
                            "error": address_details
                        }
                    )

                else:
                    data = json.dumps(
                        {
                            "result": address_details
                        }
                    )

            return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the location details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)
        
    @route('/api/v1/map/directions', methods=['GET'], auth='user', type='http')
    def get_navigation_details(self):
        """Get the navigation details
        """ 
                
        headers = [('Content-Type', 'application/json')]
                
        try:           
            profile = request.params.get('profile')
            is_roundtrip = request.params.get('is_roundtrip')
            coordinates = request.params.get('coordinates')
            status_code = 400
            
            navigation_details = naimap.get_optimized_directions_using_mapbox(coordinates)
            status_code = navigation_details.get("code")
            
            # Uncomment the following lines if you want to choose a different profile, roundtrip and coordinates
            # navigation_details = naimap.get_optimized_directions_using_mapbox(coordinates, is_roundtrip, profile)
            # status_code = navigation_details.get("code")
            
            if status_code == 404:
                data = json.dumps(
                    {
                        "error": navigation_details
                    }
                )
                
                return request.make_response(data, headers, status=status_code)
            else:
                data = json.dumps(
                    {
                        "result": navigation_details
                    }
                )
                
                return request.make_response(data, headers, status=status_code)
        except Exception as e:
            logger.exception(f"The following error occurred while fetching the navigation details:\n\n{str(e)}")
            data = json.dumps(
                {
                    "error": {
                        "code": 500,
                        "message": str(e)
                    }
                }
            )
            
            return request.make_response(data, headers, status=500)        