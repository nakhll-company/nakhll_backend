import math
from django.shortcuts import redirect
from rest_framework import views, permissions, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import GenericAPIView, CreateAPIView
from nakhll_market.models import Product
from torob_api.serializers import TorobProductListRequestSerializer, TorobProductListResponseSerializer

class TorobCustomPagination(PageNumberPagination):
    page_size = 100

    #TODO: This method should be override to get page number from post
    def get_page_number(self, request, paginator):
        # return super().get_page_number(request, paginator)
        # page_number = request.query_params.get(self.page_query_param, 1)
        page_number = request.page or 1
        if page_number in self.last_page_strings:
            page_number = paginator.num_pages
        return page_number



    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'max_pages': math.ceil(self.page.paginator.count / self.page_size),
            'products': data
        })

class TorobAllProducts(GenericAPIView):
    permission_classes = [permissions.AllowAny, ]
    pagination_class = TorobCustomPagination
    serializer_class = TorobProductListRequestSerializer
    queryset = Product.objects.all_public_products()
    page_size = 100

    def get(self, request, pk, format=None):
        product = self.get_object()
        return redirect(product.get_absolute_url())
        

    def get_queryset(self, page_url=None, page_unique=None):
        if page_url:
            Slug = page_url.split('/')[-2]
            return Product.objects.filter(Slug=Slug)
        elif page_unique:
            return Product.objects.filter(ID=page_unique)
        else:
            return Product.objects.all().order_by('-DateUpdate')

    def post(self, request, format=None):
        req_serializer = TorobProductListRequestSerializer(data=request.data)
        if req_serializer.is_valid():
            page_unique = req_serializer.validated_data.get('page_unique')
            page_url = req_serializer.validated_data.get('page_url')
            page = req_serializer.validated_data.get('page', 1)
            request.page = page
            queryset = self.filter_queryset(self.get_queryset(page_url, page_unique))

            pagin_page = self.paginate_queryset(queryset)
            if pagin_page is not None:
                serializer = TorobProductListResponseSerializer(pagin_page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = TorobProductListResponseSerializer(queryset, many=True)
            return Response(serializer.data)
        else:
            return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

