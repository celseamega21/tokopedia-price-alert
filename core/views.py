from .serializers import ProductInputSerializer, ProductOutputSerializer
from rest_framework import views, status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Product, PriceHistory
from rest_framework.response import Response
from scraper.load_balancer import LoadBalancer, clean_price
from scraper.tasks import check_price
from scraper.scraper import Scraper

class ProductListCreateView(views.APIView):
    serializer_class = ProductInputSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        user = request.user
        if user:
            products = Product.objects.filter(user=user)
        else:
            products = Product.objects.none()
        serializer = ProductOutputSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        product_url = request.data.get('url')
        email = request.data.get('email')

        if not product_url or not email:
            return Response({'error': 'Product URL and email are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        #get engine
        engine = LoadBalancer.get_scraper_engine()
        if not engine:
            return Response({"error": "No active scraper engines available"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            scraped = Scraper(product_url).scrape_product()
        except:
            return Response(
                {"error": "Failed to scraped product"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        name = scraped.get("product_name")
        price = clean_price(scraped.get("discount_price"))

        product = Product.objects.create(url=product_url, email=email, user=request.user, engine=engine, name=name, last_price=price)

        PriceHistory.objects.create(product=product, price=price)

        check_price.delay(product.id)

        return Response({"message": "Product was successfully tracked!"}, status=status.HTTP_201_CREATED)
    
class ProductDetailView(views.APIView):
    serializer_class = ProductInputSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response({"error": f"Product with ID {id} does not exist"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(product)
        return Response(serializer.data)

    def patch(self, request, id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response({"error": f"Product with ID {id} does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id):
        try:
            product = Product.objects.get(id=id)
            product.delete()
        except Product.DoesNotExist:
            return Response({"error": f"Product with ID {id} does not exist"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)