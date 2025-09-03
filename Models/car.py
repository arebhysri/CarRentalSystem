class Car:
    def __init__(self,car_id,model,manufacturer, year, mileage, is_available, min_rental_period, max_rental_period, car_rate, created_at, last_update):
        self.car_id = car_id
        self._model = model
        self._manufacturer = manufacturer
        self.year = year
        self.__mileage = mileage
        self.is_available = is_available
        self._min_rental_period = min_rental_period
        self._max_rental_period = max_rental_period
        self.__car_rate = car_rate
        self.created_at =created_at
        self.last_update = last_update

    #getter setter model
    def get_model(self):
        return self._model
    
    def set_model(self, value):
        self._model = value
    
    #getter setter manufacturer
    def get_manufacturer(self):
        return self._manufacturer
    
    def set_manufacturer(self,value):
        self._manufacturer = value

    #getter setter mileage
    def get_mileage(self):
        return self.__mileage
    
    def set_mileage(self, value):
        self.__mileage = value

    #getter setter for min_rental_period
    def get_min_rental_period(self):
        return self._min_rental_period
    
    def set_min_rental_period(self, value):
        self._min_rental_period = value

    #getter setter for maax_rental_period
    def get_max_rental_period(self):
        return self._max_rental_period
    
    def set_max_rental_period(self,value):
        self._max_rental_period = value

    #getter setter for rate
    def get_rate(self):
        return self.__car_rate
    
    def set_rate(self, value):
        self.__car_rate = value