import logging
import requests
import pytz
from datetime import datetime, date, timedelta
from odoo import models, _, fields, api
from odoo.http import request, SessionExpiredException
from odoo.exceptions import AccessDenied, AccessError, ValidationError, UserError
from .map import NaidashMap

logger = logging.getLogger(__name__)
naimap = NaidashMap()

class NaidashShipment(models.Model):
    _name = 'courier.shipment'
    _description = 'Courier Shipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id asc"

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    origin_address = fields.Char(string="Origin Address", tracking=True)
    origin_latitude = fields.Float(string="Origin Latitude", digits=(15,10), tracking=True)
    origin_longitude = fields.Float(string="Origin Longitude", digits=(15,10), tracking=True)
    destination_address = fields.Char(string="Destination Address", tracking=True)
    destination_latitude = fields.Float(string="Destination Latitude", digits=(15,10), tracking=True)
    destination_longitude = fields.Float(string="Destination Longitude", digits=(15,10), tracking=True)
    start_date = fields.Datetime(string="Start Date", tracking=True)
    end_date = fields.Datetime(string="End Date", tracking=True)
    duration = fields.Float(string="Duration(Seconds)")#, compute="_compute_duration", store=True
    distance = fields.Float(string="Distance(Metres)")# , compute="_compute_distance", store=True
    navigation_link = fields.Text(string="Navigation")# , compute="_compute_navigation", store=True
    courier_id = fields.Many2one("courier.custom", string = "Courier Id")
    courier_line_id = fields.Many2one("courier.line.custom", string = "Courier Line Id")
    
    
    @api.model
    def create(self, vals):        
        if vals.get('name', _('New')) == _('New'):
            milliseconds = (datetime.now()).strftime("%f")[:-3]
            created_date = fields.Datetime.context_timestamp(self, fields.Datetime.now()).strftime("%Y%m%d%H%M%S")
            vals['name'] = f"SH-{created_date}{milliseconds}"
        res = super(NaidashShipment, self).create(vals)
        return res
    
    def create_shipment(self, request_data):
        """Create the shipment
        """ 
        
        try:
            data = dict()
            response_data = dict()
            
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            if is_courier_manager:
                origin_address = "No Address"
                destination_address = "No Address"
                courier_id = request_data.get("courier_id")
                courier_line_id = request_data.get("courier_line_id")
                origin_latitude = request_data.get("origin_latitude")
                origin_longitude = request_data.get("origin_longitude")
                destination_longitude = request_data.get("destination_longitude")
                destination_latitude = request_data.get("destination_latitude")
                
                if not courier_id and not courier_line_id:
                    response_data["code"] = 400
                    response_data["message"] = "Bad Request! Courier id or Courier line id is required"
                    return response_data
                                                                                        
                if origin_latitude and origin_longitude:
                    src_address = naimap.reverse_geocoding_using_openstreetmap(origin_latitude, origin_longitude)
                    origin_address = src_address.get("data").get("name")                        
                    
                if destination_latitude and destination_longitude:                                                                                                                                              
                    dest_address = naimap.reverse_geocoding_using_openstreetmap(destination_latitude, destination_longitude)
                    destination_address = dest_address.get("data").get("name")                        
                
                shipment = self.env['courier.shipment'].create(
                    {
                        "courier_id": int(courier_id) if courier_id else False,
                        "courier_line_id": int(courier_line_id) if courier_line_id else False,
                        "origin_address": origin_address,
                        "origin_latitude": float(origin_latitude),
                        "origin_longitude": float(origin_longitude),
                        "destination_address": destination_address,
                        "destination_latitude": float(destination_latitude),
                        "destination_longitude": float(destination_longitude)
                    }
                )

                if shipment:
                    coordinates = f"{origin_longitude},{origin_latitude};{destination_longitude},{destination_latitude}"
                    directions = naimap.get_optimized_directions_using_mapbox(coordinates)
                    
                    if directions.get("data"):
                        # Reserved the commented code for future use
                        # origin_long = directions.get("data").get("waypoints")[0].get("location")[0]
                        # origin_lat = directions.get("data").get("waypoints")[0].get("location")[1]
                        # destination_long = directions.get("data").get("waypoints")[1].get("location")[0]
                        # destination_lat = directions.get("data").get("waypoints")[1].get("location")[1]

                        distance = directions.get("data").get("trips")[0].get("distance")
                        duration = directions.get("data").get("trips")[0].get("duration")
                        navigation_link = directions.get("data").get("trips")[0].get("directions_url")
                        
                        # Update the trip details
                        shipment.write(
                            {
                                "distance": distance,
                                "duration": duration,
                                "navigation_link": navigation_link,
                            }
                        )
                        
                        logger.info("Shipment details updated successfully")
                        
                        data['id'] = shipment.id
                        response_data["code"] = 201                
                        response_data["message"] = "Shipment created successfully"
                        response_data["data"] = data
                    else:
                        logger.error(f"Navigation Error: {directions}")
                        
                        response_data["code"] = 500
                        response_data["message"] = "Could not fetch the navigation details"
                else:
                    response_data["code"] = 500
                    response_data["message"] = "Failed to create the shipment details!"
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data
        except Exception as e:
            logger.error(f"An error ocurred while creating the shipment:\n\n{str(e)}")
            raise e
        
    def edit_shipment(self, shipment_id, request_data):
        """Edit the shipment details
        """ 
                
        try:
            response_data = dict()
            is_courier_manager = self.env.user.has_group('courier_manage.courier_management_manager_custom_group')
            
            origin_latitude = request_data.get("origin_latitude")
            origin_longitude = request_data.get("origin_longitude")
            destination_latitude = request_data.get("destination_latitude")
            destination_longitude = request_data.get("destination_longitude")            
            
            if is_courier_manager:
                shipment = self.env['courier.shipment'].browse(int(shipment_id))
                
                if shipment:
                    shipment_details = dict()
                                                                          
                    if origin_latitude and origin_longitude:
                        origin_address = naimap.reverse_geocoding_using_openstreetmap(origin_latitude, origin_longitude)
                        shipment_details["origin_address"] = origin_address.get("data").get("name")                        
                        shipment_details["origin_latitude"] = origin_address.get("data").get("lat")
                        shipment_details["origin_longitude"] = origin_address.get("data").get("lon")
                        
                    if destination_latitude and destination_longitude:                                                                                                                                              
                        destination_address = naimap.reverse_geocoding_using_openstreetmap(destination_latitude, destination_longitude)
                        shipment_details["destination_address"] = destination_address.get("data").get("name")                        
                        shipment_details["destination_latitude"] = destination_address.get("data").get("lat")
                        shipment_details["destination_longitude"] = destination_address.get("data").get("lon")                    
                        
                    # Update shipment details
                    if shipment_details:
                        shipment.write(shipment_details)
                        
                        coordinates = f"{shipment.origin_longitude},{shipment.origin_latitude};{shipment.destination_longitude},{shipment.destination_latitude}"
                        directions = naimap.get_optimized_directions_using_mapbox(coordinates)
                        
                        if directions.get("data"):
                            distance = directions.get("data").get("trips")[0].get("distance")
                            duration = directions.get("data").get("trips")[0].get("duration")
                            navigation_link = directions.get("data").get("trips")[0].get("directions_url")
                            
                            # Update the shipment details
                            shipment.write(
                                {
                                    "distance": distance,
                                    "duration": duration,
                                    "navigation_link": navigation_link,
                                }
                            )
                            
                            logger.info("Shipment details updated successfully")
                            
                            response_data["code"] = 200
                            response_data["message"] = "Updated successfully"
                        else:
                            logger.error(f"Navigation Error: {directions}")
                            
                            response_data["code"] = 500
                            response_data["message"] = "Could not fetch the navigation details"                        
                    else:
                        response_data["code"] = 204
                        response_data["message"] = "Nothing to update"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Shipment not found!"                    
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
            
            return response_data        
        except TypeError as e:
            logger.error(f"Datatype error ocurred while modifying the shipment details:\n\n{str(e)}")
            raise e        
        except Exception as e:
            logger.error(f"An error ocurred while modifying the shipment details:\n\n{str(e)}")
            raise e
        
    def get_shipment(self, shipment_id):
        """Get the shipment details
        """        
        
        try:
            data = dict()            
            response_data = dict()
            logged_in_user = self.env.user
            
            shipment = self.env['courier.shipment'].browse(int(shipment_id))
            
            if shipment:
                data["id"] = shipment.id
                data["name"] = shipment.name
                data["origin_address"] = shipment.origin_address
                data["origin_latitude"] = shipment.origin_latitude
                data["origin_longitude"] = shipment.origin_longitude
                data["destination_address"] = shipment.destination_address
                data["destination_latitude"] = shipment.destination_latitude
                data["destination_longitude"] = shipment.destination_longitude
                data["start_date"] = ""
                data["end_date"] = ""
                
                if shipment.start_date:
                    user_timezone = logged_in_user.tz or pytz.utc
                    user_timezone = pytz.timezone(user_timezone)
                    start_date = (shipment.start_date).strftime("%Y-%m-%d %H:%M")
                    start_date = datetime.strftime(
                        pytz.utc.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                        "%Y-%m-%d %H:%M"
                    )
                    
                    data["start_date"] = start_date
                    
                if shipment.end_date:
                    user_timezone = logged_in_user.tz or pytz.utc
                    user_timezone = pytz.timezone(user_timezone)
                    end_date = (shipment.end_date).strftime("%Y-%m-%d %H:%M")
                    end_date = datetime.strftime(
                        pytz.utc.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                        "%Y-%m-%d %H:%M"
                    )
                    
                    data["end_date"] = end_date 
                                                        
                data["duration"] = shipment.duration
                data["distance"] = shipment.distance
                data["navigation_link"] = shipment.navigation_link
                data["courier"] = {"id": shipment.courier_id.id, "name": shipment.courier_id.name} if shipment.courier_id else {}
                data["courier_line"] = {"id": shipment.courier_line_id.id, "name": shipment.courier_line_id.name} if shipment.courier_line_id else {}
                
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = data
            else:
                response_data["code"] = 404
                response_data["message"] = "Shipment not found!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the shipment details:\n\n{str(e)}")
            raise e
        
    def get_all_the_shipments(self, query_params):
        """Get all the shipments
        """        
        
        try:
            response_data = dict()
            all_shipments = []
            search_criteria = list()
            logged_in_user = self.env.user
            
            if query_params.get("courier_id"):
                search_criteria.append(
                    ('courier_id','=', int(query_params.get("courier_id")))
                )
                                                                    
            shipments = self.env['courier.shipment'].search(search_criteria)                
            
            if shipments:
                for shipment in shipments:
                    data = dict()
                    data["id"] = shipment.id
                    data["name"] = shipment.name
                    data["origin_address"] = shipment.origin_address
                    data["origin_latitude"] = shipment.origin_latitude
                    data["origin_longitude"] = shipment.origin_longitude
                    data["destination_address"] = shipment.destination_address
                    data["destination_latitude"] = shipment.destination_latitude
                    data["destination_longitude"] = shipment.destination_longitude
                    data["start_date"] = ""
                    data["end_date"] = ""
                    
                    if shipment.start_date:
                        user_timezone = logged_in_user.tz or pytz.utc
                        user_timezone = pytz.timezone(user_timezone)
                        start_date = (shipment.start_date).strftime("%Y-%m-%d %H:%M")
                        start_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["start_date"] = start_date
                        
                    if shipment.end_date:
                        user_timezone = logged_in_user.tz or pytz.utc
                        user_timezone = pytz.timezone(user_timezone)
                        end_date = (shipment.end_date).strftime("%Y-%m-%d %H:%M")
                        end_date = datetime.strftime(
                            pytz.utc.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M")).astimezone(user_timezone),
                            "%Y-%m-%d %H:%M"
                        )
                        
                        data["end_date"] = end_date 
                                                            
                    data["duration"] = shipment.duration
                    data["distance"] = shipment.distance
                    data["navigation_link"] = shipment.navigation_link
                    data["courier"] = {"id": shipment.courier_id.id, "name": shipment.courier_id.name} if shipment.courier_id else {}
                    data["courier_line"] = {"id": shipment.courier_line_id.id, "name": shipment.courier_line_id.name} if shipment.courier_line_id else {}
                    
                    all_shipments.append(data)
                
                response_data["code"] = 200
                response_data["message"] = "Success"
                response_data["data"] = all_shipments
            else:
                response_data["code"] = 404
                response_data["message"] = "Shipment not found!"
            
            return response_data
        except Exception as e:
            logger.error(f"The following error ocurred while fetching the shipments:\n\n{str(e)}")
            raise e
        
    def start_shipping(self, shipment_id):
        """Start shipping the package
        """ 
                
        try:
            response_data = dict()
            is_courier_user = self.env.user.has_group('courier_manage.courier_management_user_custom_group')            
            
            if is_courier_user:
                shipment = self.env['courier.shipment'].browse(int(shipment_id))
                
                if shipment:                    
                    coordinates = f"{shipment.origin_longitude},{shipment.origin_latitude};{shipment.destination_longitude},{shipment.destination_latitude}"
                    directions = naimap.get_optimized_directions_using_mapbox(coordinates)
                    
                    if directions.get("data"):
                        distance = directions.get("data").get("trips")[0].get("distance")
                        duration = directions.get("data").get("trips")[0].get("duration")
                        navigation_link = directions.get("data").get("trips")[0].get("directions_url")
                        
                        # Update the shipment details
                        shipment.write(
                            {
                                "start_date": fields.Datetime.now(),
                                "distance": distance,
                                "duration": duration,
                                "navigation_link": navigation_link,
                            }
                        )
                        
                        logger.info("Shipment details updated successfully")
                        
                        response_data["code"] = 200
                        response_data["message"] = "Updated successfully"
                    else:
                        logger.error(f"Navigation Error: {directions}")
                        
                        response_data["code"] = 500
                        response_data["message"] = "Could not fetch the navigation details"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Shipment not found!"
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
                
            return response_data        
        except TypeError as e:
            logger.error(f"Datatype error ocurred when starting to ship:\n\n{str(e)}")
            raise e        
        except Exception as e:
            logger.error(f"An error ocurred when starting to ship:\n\n{str(e)}")
            raise e

    def finish_shipping(self, shipment_id):
        """Finish shipping the package
        """ 
                
        try:
            response_data = dict()
            is_courier_user = self.env.user.has_group('courier_manage.courier_management_user_custom_group')            
            
            if is_courier_user:
                shipment = self.env['courier.shipment'].browse(int(shipment_id))
                
                if shipment:                    
                    coordinates = f"{shipment.origin_longitude},{shipment.origin_latitude};{shipment.destination_longitude},{shipment.destination_latitude}"
                    directions = naimap.get_optimized_directions_using_mapbox(coordinates)
                    
                    if directions.get("data"):
                        # Update the shipment details
                        shipment.write(
                            {
                                "end_date": fields.Datetime.now()
                            }
                        )
                        
                        logger.info("Shipment details updated successfully")
                        
                        response_data["code"] = 200
                        response_data["message"] = "Updated successfully"
                    else:
                        logger.error(f"Navigation Error: {directions}")
                        
                        response_data["code"] = 500
                        response_data["message"] = "Could not fetch the navigation details"
                else:
                    response_data["code"] = 404
                    response_data["message"] = "Shipment not found!"
            else:
                response_data["code"] = 403               
                response_data["message"] = f"{self.env.user.name}, You are not authorized to perform this action!"
                
            return response_data        
        except TypeError as e:
            logger.error(f"Datatype error ocurred when ending the shipment:\n\n{str(e)}")
            raise e        
        except Exception as e:
            logger.error(f"An error ocurred when ending the shipment:\n\n{str(e)}")
            raise e