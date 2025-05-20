''' user account management views'''
from rest_framework import generics, status, serializers
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes 
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from .services import GoogleOAuth2Service


@extend_schema(
    summary='Creating A New User',
    description='Endpoint for creating a new user. Requires email and password, other fields first name and last name',
    responses={201: UserSerializer}
)
class SignUPView(generics.CreateAPIView):
    '''local signup view'''
    permission_classes = [AllowAny]
    serializer_class = UserSerializer


@extend_schema(
    summary='Google Login Redirect',
    description='Endpoint for loging in user with google account',
    responses={301: None},
    tags=["Google Login"],
    parameters=[
        OpenApiParameter(
            name="Location",
            type=OpenApiTypes.URI,
            location=OpenApiParameter.HEADER,
            description="Google OAuth2",
            response=[301]
        )
    ]
)
class GoogleOAuth2RedirectView(APIView):
    '''Google OAuth login redirect'''
    permission_classes = [AllowAny]

    def get(self, request):
        google_oauth = GoogleOAuth2Service()

        authorization_uri = google_oauth.getAuthorizationUri()
        # request.session['google_oauth2_state'] = state

        return Response(status=status.HTTP_302_FOUND, headers={'Location': authorization_uri})

@extend_schema(exclude=True)   
class GoogleOAuth2CallbackView(APIView):
    '''google callback'''
    permission_classes = [AllowAny]

    class InnerSerializer(serializers.Serializer):
        code = serializers.CharField(required=False)
        error = serializers.CharField(required=False)

    def get(self, request):
        serializer = self.InnerSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        code = data.get('code')

        if 'error' in data:
            return Response({'error': data.get('error')}, status=status.HTTP_401_UNAUTHORIZED)

        if not code:
            return Response({'error': "code is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        google_oauth = GoogleOAuth2Service()
        google_tokens = google_oauth.getTokens(code)
        try:
            user_info = google_oauth.decodeIdToken(google_tokens)
        except Exception as e:
            return Response({'error': "invalid token type"}, status=status.HTTP_400_BAD_REQUEST)
        app_tokens = google_oauth.getTokenForUser(user_info)

        return Response({'access_token': str(app_tokens.access_token), 'refresh_token': str(app_tokens)})


class GoogleOauth2MobileAuth(APIView):
    permission_classes = [AllowAny]

    class InnerSerializer(serializers.Serializer):
        id_token = serializers.CharField(required=True)
        access_token = serializers.CharField(required=True)
        error = serializers.CharField(required=False)
    

    def post(self, request):
        serializer = self.InnerSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            print(e)
        data = serializer.validated_data
        id_token = data.get('id_token')
        access_token = data.get('access_token')

        if not id_token or not access_token:
            return Response({'error': "Both id_token and access_token are required"}, status=status.HTTP_400_BAD_REQUEST)

        google_oauth = GoogleOAuth2Service()

        try:
            user_info = google_oauth.decodeIdToken({'id_token': id_token})
        except Exception as e:
            return Response({'error': f"Invalid ID token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        app_tokens = google_oauth.getTokenForUser(user_info)

        return Response({'access_token': str(app_tokens.access_token), 'refresh_token': str(app_tokens)})


@extend_schema(
    summary="Login User",
    description='Endpoint to log user into the system, required email and password.',
    responses={200: TokenRefreshSerializer}
)
class CustomTokenObtainPairView(TokenObtainPairView):
    '''user login view'''
    serializer_class = CustomTokenObtainPairSerializer
