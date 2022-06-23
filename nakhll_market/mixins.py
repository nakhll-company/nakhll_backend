class DriveBigCityAndStateFromCityMixin:
    city_field = 'City'
    big_city_field = 'BigCity'
    state_field = 'State'

    def create(self, validated_data):
        city = validated_data.get(self.city_field)
        validated_data[self.big_city_field] = city.big_city
        validated_data[self.state_field] = city.big_city.state
        return super().create(validated_data)
