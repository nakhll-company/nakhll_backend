from django_filters import rest_framework as filters
from nakhll_market.models import BigCity, City, Category, Product, State, Tag, ProductTag
from nakhll_market.utils import split_args


class ProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="Price", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="Price", lookup_expr='lte')
    ready = filters.BooleanFilter(method='filter_ready')
    search = filters.CharFilter(method='filter_search')
    q = filters.CharFilter(method='filter_q')
    available = filters.BooleanFilter(method='filter_available')
    category = filters.CharFilter(method='filter_category')
    city = filters.CharFilter(method='filter_city')
    big_city = filters.CharFilter(method='filter_big_city')
    state = filters.CharFilter(method='filter_state')
    tags = filters.CharFilter(method='filter_tags')
    discounted = filters.BooleanFilter(method='filter_discounted')
    shop = filters.CharFilter(method='filter_shop')
    in_campaign = filters.BooleanFilter(method='filter_in_campaign')

    class Meta:
        model = Product
        fields = [
            'search',
            'min_price',
            'max_price',
            'ready',
            'available',
            'category',
            'in_campaign',
            'category',
            'city',
            'discounted',
            'is_advertisement',
            'shop']

    def filter_ready(self, queryset, name, value):
        READY_IN_STOCK = '1'
        filter_queryset = {'Status': READY_IN_STOCK, 'Inventory__gt': 0}
        return queryset.filter(**filter_queryset) if value else queryset

    def filter_search(self, queryset, name, value):
        return queryset.filter(Title__icontains=value)

    def filter_q(self, queryset, name, value):
        return queryset.filter(Title__icontains=value)

    def filter_available(self, queryset, name, value):
        if value:
            AVAILABLE_IDS = ['1', '2', '3', ]
            return queryset.filter(
                Status__in=AVAILABLE_IDS, Inventory__gt=0,
                FK_Shop__Publish=True)
        return queryset

    @split_args(-1)
    def filter_category(self, queryset, name, value):
        return queryset.filter(
            category__in=value) if value else queryset

    @split_args(-1)
    def filter_category(self, queryset, name, value):
        categories = Category.objects.filter(id__in=value)
        subcategories = Category.objects.all_subcategories(categories)
        return queryset.filter(category__in=subcategories)

    # TODO: in all shops or in owenshop?

    @split_args(-1)
    def filter_tags(self, queryset, name, value):
        product_id = ProductTag.objects.filter(
            tag__id__in=value).values_list(
            'product', flat=True)
        return queryset.filter(ID__in=product_id)

    @split_args(-1)
    def filter_state(self, queryset, name, value):
        states = State.objects.filter(
            id__in=value).values_list(
            'id', flat=True)
        return queryset.filter(FK_Shop__State__in=states)

    @split_args(-1)
    def filter_big_city(self, queryset, name, value):
        big_cities = BigCity.objects.filter(
            id__in=value).values_list(
            'id', flat=True)
        return queryset.filter(FK_Shop__BigCity__in=big_cities)

    @split_args(-1)
    def filter_city(self, queryset, name, value):
        cities = City.objects.filter(
            id__in=value).values_list(
            'id', flat=True)
        return queryset.filter(FK_Shop__City__in=cities)

    def filter_discounted(self, queryset, name, value):
        return queryset.filter(OldPrice__gt=0) if value else queryset

    def filter_shop(self, queryset, name, value):
        return queryset.filter(FK_Shop__Slug=value)

    def filter_in_campaign(self, queryset, name, value):
        return queryset.filter(FK_Shop__in_campaign=True)
