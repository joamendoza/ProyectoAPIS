"""
Integración con Webpay Plus para pagos
"""
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions
import uuid
from datetime import datetime

# Configuración de Webpay (Ambiente de pruebas)
try:
    from transbank import configuration
    configuration.integration_type = IntegrationType.TEST
    configuration.commerce_code = "597055555532"
    configuration.api_key = "579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C"
except ImportError:
    # Fallback para versiones más nuevas de Transbank
    pass

class WebpayIntegration:
    """Clase para manejar las integraciones con Webpay"""
    
    @staticmethod
    def crear_transaccion(amount, order_id, return_url):
        """Crear una transacción en Webpay"""
        try:
            # Crear la transacción
            transaction = Transaction()
            response = transaction.create(
                buy_order=order_id,
                amount=amount,
                return_url=return_url
            )
            
            return {
                'success': True,
                'token': response.token,
                'url': response.url,
                'order_id': order_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def confirmar_transaccion(token):
        """Confirmar una transacción en Webpay"""
        try:
            transaction = Transaction()
            response = transaction.commit(token)
            
            return {
                'success': True,
                'authorization_code': response.authorization_code,
                'amount': response.amount,
                'buy_order': response.buy_order,
                'transaction_date': response.transaction_date,
                'response_code': response.response_code,
                'status': response.status
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def generar_order_id():
        """Generar un ID único para la orden"""
        return str(uuid.uuid4())[:8].upper()

def iniciar_pago_webpay(request, total, usuario_id):
    """Iniciar proceso de pago con Webpay"""
    try:
        # Generar orden única
        order_id = WebpayIntegration.generar_order_id()
        
        # URL de retorno
        return_url = request.build_absolute_uri(reverse('ferremas_mongo:webpay_return'))
        
        # Crear transacción
        result = WebpayIntegration.crear_transaccion(
            amount=int(total),
            order_id=order_id,
            return_url=return_url
        )
        
        if result['success']:
            # Guardar información de la transacción en sesión
            request.session['webpay_order_id'] = order_id
            request.session['webpay_amount'] = int(total)
            request.session['webpay_usuario_id'] = usuario_id
            
            return {
                'success': True,
                'url': result['url'],
                'token': result['token'],
                'order_id': order_id
            }
        else:
            return {
                'success': False,
                'error': result['error']
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@api_view(['POST'])
def webpay_return(request):
    """Endpoint para manejar el retorno de Webpay"""
    try:
        token = request.data.get('token_ws') or request.GET.get('token_ws')
        
        if not token:
            return Response({'error': 'Token no encontrado'}, status=400)
        
        # Confirmar transacción
        result = WebpayIntegration.confirmar_transaccion(token)
        
        if result['success'] and result['response_code'] == 0:
            # Pago exitoso
            return Response({
                'success': True,
                'message': 'Pago procesado exitosamente',
                'authorization_code': result['authorization_code'],
                'amount': result['amount'],
                'buy_order': result['buy_order']
            })
        else:
            # Pago fallido
            return Response({
                'success': False,
                'error': 'Pago no autorizado',
                'response_code': result.get('response_code', -1)
            }, status=400)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
