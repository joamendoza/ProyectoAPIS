"""
Integración con BCCH (Banco Central de Chile) para obtener tipos de cambio
"""
import requests
from bcchapi import BcchApi
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from datetime import datetime, timedelta
import json
import os

class BCCHIntegration:
    """Clase para manejar las integraciones con BCCH"""
    
    def __init__(self):
        # Configuración de BCCH API
        self.bcch_api = BcchApi(
            username="admin@admin.cl",  # Usuario de prueba
            password="admin123"  # Contraseña de prueba
        )
        self.cache_duration = 3600  # 1 hora
    
    def obtener_tipo_cambio(self, moneda_origen='CLP', moneda_destino='USD'):
        """Obtener tipo de cambio entre dos monedas"""
        try:
            # Revisar cache primero
            cache_key = f"bcch_tipo_cambio_{moneda_origen}_{moneda_destino}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                return cached_result
            
            # Si no está en cache, obtener desde BCCH
            if moneda_origen == 'CLP' and moneda_destino == 'USD':
                # Obtener USD/CLP
                result = self.bcch_api.get_macro_indicator(
                    indicator='F073.TCO.PRE.Z.D',
                    start_date='2024-01-01',
                    end_date='2024-12-31'
                )
                
                if result and result.get('data'):
                    # Obtener el valor más reciente
                    latest_value = result['data'][-1]['value']
                    tipo_cambio = {
                        'moneda_origen': moneda_origen,
                        'moneda_destino': moneda_destino,
                        'valor': float(latest_value),
                        'fecha': datetime.now().isoformat(),
                        'fuente': 'BCCH'
                    }
                    
                    # Guardar en cache
                    cache.set(cache_key, tipo_cambio, self.cache_duration)
                    return tipo_cambio
            
            # Valores por defecto si no se puede obtener desde BCCH
            return self.obtener_tipo_cambio_fallback(moneda_origen, moneda_destino)
            
        except Exception as e:
            print(f"Error obteniendo tipo de cambio desde BCCH: {e}")
            return self.obtener_tipo_cambio_fallback(moneda_origen, moneda_destino)
    
    def obtener_tipo_cambio_fallback(self, moneda_origen='CLP', moneda_destino='USD'):
        """Obtener tipo de cambio de respaldo usando API pública"""
        try:
            # Usar API pública como respaldo
            url = f"https://api.exchangerate-api.com/v4/latest/{moneda_origen}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if moneda_destino in data['rates']:
                    return {
                        'moneda_origen': moneda_origen,
                        'moneda_destino': moneda_destino,
                        'valor': data['rates'][moneda_destino],
                        'fecha': datetime.now().isoformat(),
                        'fuente': 'ExchangeRate-API'
                    }
            
            # Si todo falla, usar valores fijos
            tipos_cambio_fijos = {
                ('CLP', 'USD'): 0.0011,  # 1 CLP = 0.0011 USD
                ('USD', 'CLP'): 900.0,   # 1 USD = 900 CLP
                ('CLP', 'EUR'): 0.0010,  # 1 CLP = 0.0010 EUR
                ('EUR', 'CLP'): 1000.0,  # 1 EUR = 1000 CLP
            }
            
            valor = tipos_cambio_fijos.get((moneda_origen, moneda_destino), 1.0)
            return {
                'moneda_origen': moneda_origen,
                'moneda_destino': moneda_destino,
                'valor': valor,
                'fecha': datetime.now().isoformat(),
                'fuente': 'Valor_fijo'
            }
            
        except Exception as e:
            print(f"Error en tipo de cambio fallback: {e}")
            return {
                'moneda_origen': moneda_origen,
                'moneda_destino': moneda_destino,
                'valor': 1.0,
                'fecha': datetime.now().isoformat(),
                'fuente': 'Error_fallback'
            }
    
    def convertir_moneda(self, amount, moneda_origen='CLP', moneda_destino='USD'):
        """Convertir un monto entre monedas"""
        try:
            tipo_cambio = self.obtener_tipo_cambio(moneda_origen, moneda_destino)
            amount_convertido = float(amount) * tipo_cambio['valor']
            
            return {
                'amount_original': amount,
                'moneda_origen': moneda_origen,
                'amount_convertido': round(amount_convertido, 2),
                'moneda_destino': moneda_destino,
                'tipo_cambio': tipo_cambio['valor'],
                'fecha': tipo_cambio['fecha'],
                'fuente': tipo_cambio['fuente']
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'amount_original': amount,
                'amount_convertido': amount  # Devolver el mismo monto si hay error
            }
    
    def obtener_indicadores_economicos(self):
        """Obtener indicadores económicos principales"""
        try:
            cache_key = "bcch_indicadores_economicos"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                return cached_result
            
            # Obtener varios indicadores
            indicadores = {
                'uf': self.obtener_uf(),
                'utm': self.obtener_utm(),
                'dolar': self.obtener_tipo_cambio('USD', 'CLP'),
                'euro': self.obtener_tipo_cambio('EUR', 'CLP')
            }
            
            # Guardar en cache por 1 hora
            cache.set(cache_key, indicadores, 3600)
            return indicadores
            
        except Exception as e:
            print(f"Error obteniendo indicadores: {e}")
            return {
                'error': str(e),
                'uf': {'valor': 37000, 'fuente': 'Valor_fijo'},
                'utm': {'valor': 65000, 'fuente': 'Valor_fijo'},
                'dolar': {'valor': 900, 'fuente': 'Valor_fijo'},
                'euro': {'valor': 1000, 'fuente': 'Valor_fijo'}
            }
    
    def obtener_uf(self):
        """Obtener valor de la UF"""
        try:
            # Simular obtención de UF
            return {
                'valor': 37000,  # Valor aproximado
                'fecha': datetime.now().isoformat(),
                'fuente': 'BCCH_simulado'
            }
        except Exception as e:
            return {
                'valor': 37000,
                'fecha': datetime.now().isoformat(),
                'fuente': 'Valor_fijo',
                'error': str(e)
            }
    
    def obtener_utm(self):
        """Obtener valor de la UTM"""
        try:
            # Simular obtención de UTM
            return {
                'valor': 65000,  # Valor aproximado
                'fecha': datetime.now().isoformat(),
                'fuente': 'BCCH_simulado'
            }
        except Exception as e:
            return {
                'valor': 65000,
                'fecha': datetime.now().isoformat(),
                'fuente': 'Valor_fijo',
                'error': str(e)
            }

# Instancia global
bcch_integration = BCCHIntegration()

@api_view(['GET'])
def obtener_tipo_cambio_api(request):
    """API endpoint para obtener tipos de cambio"""
    try:
        moneda_origen = request.GET.get('origen', 'CLP')
        moneda_destino = request.GET.get('destino', 'USD')
        
        resultado = bcch_integration.obtener_tipo_cambio(moneda_origen, moneda_destino)
        return Response(resultado)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def convertir_moneda_api(request):
    """API endpoint para convertir monedas"""
    try:
        amount = float(request.GET.get('amount', 0))
        moneda_origen = request.GET.get('origen', 'CLP')
        moneda_destino = request.GET.get('destino', 'USD')
        
        resultado = bcch_integration.convertir_moneda(amount, moneda_origen, moneda_destino)
        return Response(resultado)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def obtener_indicadores_api(request):
    """API endpoint para obtener indicadores económicos"""
    try:
        resultado = bcch_integration.obtener_indicadores_economicos()
        return Response(resultado)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)
