#!/usr/bin/env python3
"""
Age of Conquest IV - Simulador con Interfaz Gráfica y Modo Consola
VERSIÓN COMPLETA - Todo en un solo archivo
Requiere: pip install PyQt5

Curso: Simulación de Sistemas - UNET
Integrantes: Bryant Vivas, Ángel Sanchez, Leynner Angulo
Agosto 2026

"""

import sys
import random
import math
from datetime import datetime
from enum import Enum

# ==========================================
# CONSTANTES Y FUNCIONES AUXILIARES
# ==========================================

def Sat(x):
    """Funcion de saturacion [0, 100]"""
    return max(0.0, min(100.0, x))

def clamp(x, min_val, max_val):
    """Funcion de clamp generica"""
    return max(min_val, min(max_val, x))

class TipoEvento(Enum):
    """Tipos de eventos para la LEF"""
    FIN_DE_TURNO = 1
    BATALLA = 2
    RECLUTAMIENTO = 3
    MUERTE_REY = 4
    FIESTA = 5
    EVENTO_ALEATORIO = 6

# ==========================================
# CLASES DEL MODELO
# ==========================================

class EventoSIM:
    """Estructura para la Lista de Eventos Futuros (LEF)"""
    def __init__(self, turno_ejecucion, tipo, datos=None):
        self.turno_ejecucion = turno_ejecucion
        self.tipo = tipo
        self.datos = datos or {}
        
    def __lt__(self, other):
        return self.turno_ejecucion < other.turno_ejecucion

class Provincia:
    def __init__(self, nombre, propietario, poblacion, tropas, felicidad=80.0, es_capital=False):
        self.nombre = nombre
        self.propietario = propietario
        self.poblacion = poblacion
        self.tropas = tropas
        self.felicidad = felicidad
        self.es_capital = es_capital
        self.activa = True  # Para manejar provincias deshabitadas
        self.turnos_huelga = 0  # Para metricas TMH
        
    def __str__(self):
        estado = " CAPITAL" if self.es_capital else ""
        return f"{self.nombre} ({self.propietario}) | Pob: {self.poblacion:,} | Tropas: {self.tropas} | Fel: {self.felicidad:.1f}% {estado}"

class Imperio:
    def __init__(self, nombre, oro=500, tasa_impuestos=1.0, es_ia=True):
        self.nombre = nombre
        self.oro = oro
        self.tasa_impuestos = tasa_impuestos
        self.es_protectorado = False
        self.rey_vivo = True
        self.provincias_conquistadas = 0
        self.puntos_movimiento = 3
        self.puntos_movimiento_max = 3
        self.es_ia = es_ia  # True = controlado por IA
        
        # Metricas de rendimiento
        self.turnos_flujo_positivo = 0
        self.turnos_totales = 0
        self.bajas_infligidas = 0
        self.bajas_recibidas = 0
        self.provincias_anexadas = 0
        
        # Historial de felicidad para metricas
        self.historial_felicidad = []
        
    def reset_puntos(self):
        self.puntos_movimiento = self.puntos_movimiento_max
        
    def tiene_puntos(self):
        return self.puntos_movimiento > 0
        
    def gastar_punto(self):
        if self.tiene_puntos():
            self.puntos_movimiento -= 1
            return True
        return False
        
    def __str__(self):
        estado = "Protectorado" if self.es_protectorado else "Libre"
        rey = "Vivo" if self.rey_vivo else "Muerto"
        ia = "IA" if self.es_ia else "Jugador"
        return f"{self.nombre} | Oro: {self.oro:.1f} | {estado} | Rey: {rey} | {ia}"

# ==========================================
# MOTOR DE SIMULACION
# ==========================================

class MotorSimulacion:
    def __init__(self, modo_consola=False):
        self.turno_actual = 0
        self.imperios = {}
        self.mapa = {}
        self.estadisticas_turnos = []
        self.log_historial = []
        self.imperio_jugador = "Imperio Romano"
        self.modo_consola = modo_consola
        
        # Lista de Eventos Futuros (LEF) - Mantenida por compatibilidad
        self.lef = []
        
        # Bandera para evitar procesamiento recursivo de IA
        self.procesando_ia = False
        
        # Parametros del juego (calibrados segun documentos)
        self.parametros = {
            'alfa': 0.05,           # Coeficiente tributario
            'm_div': 20.0,          # Divisor logistico de mantenimiento
            'delta': 8.0,           # Penalizacion por impuestos
            'gamma': 10.0,          # Bonificacion por fiesta
            'delta_hrey': 20.0,     # Penalizacion por muerte del rey
            'p_muerte': 0.25,       # Probabilidad de muerte del rey
            'h_huelga': 50.0,       # Umbral de huelga fiscal
            'tributo': 0.10,        # Tasa de vasallaje
            'crecimiento': 1.01,    # Tasa de crecimiento poblacional
            'decrecimiento': 0.99,  # Tasa de decrecimiento poblacional
            'p_evento': 0.05,       # Probabilidad de evento aleatorio
        }
        
        self._configurar_juego()
        
        if self.modo_consola:
            self._mostrar_bienvenida_consola()
        
    def _configurar_juego(self):
        """Configuracion inicial del juego"""
        # Imperios (el jugador es el primero)
        imperios_data = [
            ("Imperio Romano", 500, 1.0, False),   # Jugador
            ("Tribus Galas", 200, 0.8, True),      # IA
            ("Egipcios", 300, 0.9, True),          # IA
            ("Griegos", 250, 0.85, True)           # IA
        ]
        
        for nombre, oro, imp, es_ia in imperios_data:
            self.imperios[nombre] = Imperio(nombre, oro, imp, es_ia)
            
        # Provincias
        provincias_data = [
            ("Roma", "Imperio Romano", 10000, 200, 80, True),
            ("Galia", "Tribus Galas", 5000, 150, 75, True),
            ("Egipto", "Egipcios", 8000, 180, 70, True),
            ("Atenas", "Griegos", 6000, 130, 85, True),
            ("Cartago", "Imperio Romano", 4000, 100, 60, False),
            ("Germania", "Tribus Galas", 3000, 80, 55, False),
            ("Macedonia", "Griegos", 3500, 90, 65, False),
            ("Siria", "Egipcios", 4500, 110, 60, False),
        ]
        
        for nombre, prop, pob, trop, fel, capital in provincias_data:
            self.mapa[nombre] = Provincia(nombre, prop, pob, trop, fel, capital)
            
        # Inicializar LEF con evento de fin de turno
        self.lef.append(EventoSIM(1, TipoEvento.FIN_DE_TURNO))
        self.lef.append(EventoSIM(2, TipoEvento.EVENTO_ALEATORIO))

    def _mostrar_bienvenida_consola(self):
        """Muestra mensaje de bienvenida en modo consola"""
        print("=" * 60)
        print("  AGE OF CONQUEST IV - SIMULADOR (MODO CONSOLA)")
        print("=" * 60)
        print("\nImperios:")
        for nombre, imp in self.imperios.items():
            print(f"  - {nombre}: {imp.oro} oro, {'Jugador' if not imp.es_ia else 'IA'}")
        print("\nProvincias iniciales:")
        for nombre, p in self.mapa.items():
            print(f"  - {nombre}: {p.propietario} (Pob: {p.poblacion}, Tropas: {p.tropas})")
        print("\n" + "=" * 60)
        print("Comandos disponibles:")
        print("  r <provincia> <cantidad>  - Reclutar tropas")
        print("  a <origen> <destino> <tropas> [rey] - Atacar (rey=s/n)")
        print("  f <provincia>             - Organizar fiesta")
        print("  i <imperio> <tasa>        - Cambiar impuestos")
        print("  t                         - Avanzar un turno")
        print("  5                         - Avanzar 5 turnos")
        print("  s                         - Ver estado")
        print("  m                         - Ver metricas")
        print("  ia                        - Ejecutar IA enemiga")
        print("  q                         - Salir")
        print("=" * 60)

    def obtener_provincia(self, nombre):
        for p in self.mapa.values():
            if p.nombre.lower() == nombre.lower():
                return p
        return None

    def obtener_imperio(self, nombre):
        for i in self.imperios.values():
            if i.nombre.lower() == nombre.lower():
                return i
        return None

    def provincias_de(self, nombre):
        return [p for p in self.mapa.values() if p.propietario == nombre and p.activa]

    def provincias_enemigas(self, nombre):
        return [p for p in self.mapa.values() if p.propietario != nombre and p.activa]

    # ==========================================
    # ACCIONES DEL JUGADOR
    # ==========================================

    def reclutar_tropas(self, provincia, cantidad):
        p = self.obtener_provincia(provincia)
        if not p:
            return {'success': False, 'error': f"Provincia '{provincia}' no encontrada"}
        if not p.activa:
            return {'success': False, 'error': f"Provincia '{provincia}' esta deshabitada"}
        
        imp = self.obtener_imperio(p.propietario)
        if not imp:
            return {'success': False, 'error': "Imperio no encontrado"}
        if not imp.tiene_puntos():
            return {'success': False, 'error': "Sin puntos de movimiento"}
        if imp.oro < cantidad * 2:
            return {'success': False, 'error': f"Oro insuficiente. Necesitas {cantidad * 2:.1f}"}
        if p.poblacion < cantidad:
            return {'success': False, 'error': f"Poblacion insuficiente. Tienes {p.poblacion}"}
            
        imp.oro -= cantidad * 2
        p.poblacion -= cantidad
        p.tropas += cantidad
        imp.gastar_punto()
        
        return {'success': True, 'provincia': p.nombre, 'cantidad': cantidad}

    def organizar_fiesta(self, provincia):
        p = self.obtener_provincia(provincia)
        if not p:
            return {'success': False, 'error': f"Provincia '{provincia}' no encontrada"}
        if not p.activa:
            return {'success': False, 'error': f"Provincia '{provincia}' esta deshabitada"}
            
        imp = self.obtener_imperio(p.propietario)
        if not imp:
            return {'success': False, 'error': "Imperio no encontrado"}
        if not imp.tiene_puntos():
            return {'success': False, 'error': "Sin puntos de movimiento"}
        if imp.oro < 50:
            return {'success': False, 'error': f"Oro insuficiente. Necesitas 50"}
            
        imp.oro -= 50
        nueva_felicidad = Sat(p.felicidad + self.parametros['gamma'])
        p.felicidad = nueva_felicidad
        imp.gastar_punto()
        
        return {'success': True, 'provincia': p.nombre, 'nueva_felicidad': p.felicidad}

    def cambiar_impuestos(self, nombre_imperio, nueva_tasa):
        imp = self.obtener_imperio(nombre_imperio)
        if not imp:
            return {'success': False, 'error': f"Imperio '{nombre_imperio}' no encontrado"}
        if nueva_tasa < 0:
            return {'success': False, 'error': "La tasa no puede ser negativa"}
        antigua = imp.tasa_impuestos
        imp.tasa_impuestos = nueva_tasa
        return {'success': True, 'antigua_tasa': antigua, 'nueva_tasa': nueva_tasa}

    def atacar_provincia(self, origen, destino, tropas, rey_presente=False):
        o = self.obtener_provincia(origen)
        d = self.obtener_provincia(destino)
        
        if not o or not d:
            return {'success': False, 'error': "Provincia no encontrada"}
        if not o.activa or not d.activa:
            return {'success': False, 'error': "Provincia deshabitada"}
        if o.propietario == d.propietario:
            return {'success': False, 'error': "No se puede atacar a si mismo"}
            
        imp = self.obtener_imperio(o.propietario)
        if not imp:
            return {'success': False, 'error': "Imperio no encontrado"}
        if not imp.tiene_puntos():
            return {'success': False, 'error': "Sin puntos de movimiento"}
        if o.tropas < tropas:
            return {'success': False, 'error': f"Tropas insuficientes. Tienes {o.tropas}"}
        if tropas <= 0:
            return {'success': False, 'error': "Debes enviar al menos 1 soldado"}
            
        o.tropas -= tropas
        A = float(tropas)
        D = float(d.tropas)
        mu = 1.25 if rey_presente and imp.rey_vivo else 1.0
        ea = 0.10 * mu
        ed = 0.10
        
        # Simulacion de batalla (Lanchester estocastico)
        asaltos = 0
        while A > 0 and D > 0 and asaltos < 100:
            asaltos += 1
            # El atacante recibe dano del defensor
            A = max(0, A - D * ed * random.uniform(0.7, 1.3))
            # El defensor recibe dano del atacante
            D = max(0, D - A * ea * random.uniform(0.7, 1.3))
            
        A, D = int(A), int(D)
        imp.gastar_punto()
        
        # Registrar bajas
        imp.bajas_infligidas += abs(tropas - A) if A > 0 else tropas
        imp.bajas_recibidas += tropas - A if tropas > A else 0
        
        if A > 0:
            # VICTORIA - Conquista
            imp.provincias_conquistadas += 1
            imp.provincias_anexadas += 1
            
            # Transferir provincia
            d.propietario = o.propietario
            d.tropas = A
            d.poblacion = int(d.poblacion * 0.7)
            if d.poblacion <= 0:
                d.poblacion = 1
                d.activa = True
            
            return {'success': True, 'victoria': True, 'provincia': d.nombre, 'tropas': A}
        else:
            # DERROTA
            d.tropas = D
            o.felicidad = Sat(o.felicidad - self.parametros['delta'])
            
            # Verificar muerte del rey
            if rey_presente and imp.rey_vivo and random.random() <= self.parametros['p_muerte']:
                imp.rey_vivo = False
                imp.es_protectorado = True
                o.felicidad = Sat(o.felicidad - self.parametros['delta_hrey'])
                
                return {'success': True, 'victoria': False, 'rey_muerto': True, 'provincia': d.nombre}
                
            return {'success': True, 'victoria': False, 'provincia': d.nombre}

    # ==========================================
    # INTELIGENCIA ARTIFICIAL
    # ==========================================

    def tomar_decision_ia(self, imperio):
        """Arbol de decision para imperios controlados por IA"""
        if not imperio.es_ia or imperio.nombre == self.imperio_jugador:
            return None
            
        provincias = self.provincias_de(imperio.nombre)
        if not provincias:
            return None
            
        felicidad_promedio = sum(p.felicidad for p in provincias) / len(provincias)
        tropas_totales = sum(p.tropas for p in provincias)
        
        # 1. VERIFICAR ESTABILIDAD INTERNA
        if felicidad_promedio < self.parametros['h_huelga']:
            # Crisis social - Priorizar felicidad
            if imperio.oro >= 100:
                # Organizar fiesta en la provincia mas infeliz
                peor = min(provincias, key=lambda p: p.felicidad)
                return self.organizar_fiesta(peor.nombre)
            else:
                # Reducir impuestos
                nueva_tasa = max(0, imperio.tasa_impuestos - 0.2)
                return self.cambiar_impuestos(imperio.nombre, nueva_tasa)
        
        # 2. EVALUAR SITUACION ECONOMICA
        if imperio.oro < 50:
            # Necesita ingresos - Subir impuestos
            nueva_tasa = min(2.0, imperio.tasa_impuestos + 0.2)
            return self.cambiar_impuestos(imperio.nombre, nueva_tasa)
        
        # 3. EVALUAR OPORTUNIDADES MILITARES
        enemigos = self.provincias_enemigas(imperio.nombre)
        if enemigos and tropas_totales > 50:
            # Buscar provincia enemiga debil
            enemigo_debil = min(enemigos, key=lambda p: p.tropas)
            if enemigo_debil.tropas < tropas_totales * 0.6:
                # Atacar
                origen = max(provincias, key=lambda p: p.tropas)
                tropas_a_enviar = min(origen.tropas - 10, int(tropas_totales * 0.5))
                if tropas_a_enviar > 0:
                    return self.atacar_provincia(origen.nombre, enemigo_debil.nombre, 
                                                 tropas_a_enviar, random.random() < 0.3)
        
        # 4. RECLUTAR SI HAY RECURSOS
        if imperio.oro > 300 and tropas_totales < 500:
            mejor = max(provincias, key=lambda p: p.poblacion)
            cantidad = min(50, int(mejor.poblacion * 0.05))
            if cantidad > 0:
                return self.reclutar_tropas(mejor.nombre, cantidad)
        
        return None

    def procesar_ia_turno(self):
        """Procesa las decisiones de IA para todos los imperios enemigos"""
        if self.procesando_ia:
            return []  # Evitar recursion
            
        self.procesando_ia = True
        resultados = []
        try:
            for nombre, imp in self.imperios.items():
                if imp.es_ia and imp.nombre != self.imperio_jugador:
                    resultado = self.tomar_decision_ia(imp)
                    if resultado and resultado.get('success'):
                        resultados.append(f"{nombre}: Accion IA ejecutada")
        finally:
            self.procesando_ia = False
        return resultados

    # ==========================================
    # PROCESAMIENTO DE TURNOS (EVENTOS)
    # ==========================================

    def procesar_fin_de_turno(self):
        """Procesa el evento de fin de turno (evento sincrono principal)"""
        self.turno_actual += 1
        resumen = {}
        
        for nombre, imp in self.imperios.items():
            provincias = self.provincias_de(nombre)
            if not provincias:
                resumen[nombre] = {'ingresos': 0, 'mantenimiento': 0, 'tributo': 0, 'oro': imp.oro, 'felicidad_promedio': 0}
                continue
                
            ingresos = 0
            mantenimiento = 0
            felicidad_promedio = 0
            
            for p in provincias:
                # 1. DINAMICA DEMOGRAFICA
                if p.felicidad >= self.parametros['h_huelga']:
                    p.poblacion = int(p.poblacion * self.parametros['crecimiento'])
                else:
                    p.poblacion = int(p.poblacion * self.parametros['decrecimiento'])
                    p.turnos_huelga += 1  # Para metrica TMH
                
                # Validacion de poblacion minima
                if p.poblacion <= 0:
                    p.poblacion = 0
                    p.activa = False
                    # Las tropas desaparecen si no hay poblacion
                    p.tropas = 0
                    continue
                
                # 2. ACTUALIZACION DE FELICIDAD
                # Penalizacion por impuestos
                penalizacion = self.parametros['delta'] * imp.tasa_impuestos
                p.felicidad = Sat(p.felicidad - penalizacion)
                
                # Bonificacion si tasa = 0 (segun documento)
                if imp.tasa_impuestos == 0:
                    p.felicidad = Sat(p.felicidad + 10)
                
                # Si es protectorado, bonificacion extra
                if imp.es_protectorado:
                    p.felicidad = Sat(p.felicidad * 1.03)
                
                # 3. RECAUDACION IMPOSITIVA CONDICIONAL
                rec = 0
                if p.felicidad >= self.parametros['h_huelga'] and p.activa:
                    rec = p.poblacion * self.parametros['alfa'] * imp.tasa_impuestos
                    ingresos += rec
                else:
                    p.turnos_huelga += 1
                
                # 4. MANTENIMIENTO MILITAR (con suelo minimo)
                if p.tropas > 0:
                    mant = max(1, math.floor(p.tropas / self.parametros['m_div']))
                    mantenimiento += mant
                
                felicidad_promedio += p.felicidad
            
            felicidad_promedio = felicidad_promedio / len(provincias) if provincias else 0
            imp.historial_felicidad.append(felicidad_promedio)
            
            # 5. TRIBUTO POR PROTECTORADO
            tributo = 0
            if imp.es_protectorado:
                tributo = ingresos * self.parametros['tributo']
                ingresos -= tributo
            
            # 6. BALANCE FINAL DE TESORERIA
            imp.oro = imp.oro + ingresos - mantenimiento
            
            # Registrar metricas
            imp.turnos_totales += 1
            if imp.oro > 0 and ingresos > mantenimiento:
                imp.turnos_flujo_positivo += 1
            
            resumen[nombre] = {
                'ingresos': round(ingresos, 1),
                'mantenimiento': round(mantenimiento, 1),
                'tributo': round(tributo, 1),
                'oro': round(imp.oro, 1),
                'felicidad_promedio': round(felicidad_promedio, 1)
            }
        
        # Registrar estadisticas
        self.estadisticas_turnos.append({
            'turno': self.turno_actual, 
            'resumen': resumen
        })
        
        # Procesar IA despues del turno
        resultados_ia = self.procesar_ia_turno()
        
        # Evento aleatorio
        if random.random() < self.parametros['p_evento']:
            self._evento_aleatorio()
        
        # Resetear puntos de movimiento para todos los imperios
        for imp in self.imperios.values():
            imp.reset_puntos()
        
        return resumen, resultados_ia

    def _evento_aleatorio(self):
        """Evento aleatorio segun el documento"""
        imp = random.choice(list(self.imperios.values()))
        tipo = random.choice(['peste', 'cosecha', 'tesoro', 'terremoto'])
        
        if tipo == 'peste':
            for p in self.provincias_de(imp.nombre):
                p.poblacion = int(p.poblacion * 0.9)
                p.felicidad = Sat(p.felicidad - 15)
                if p.poblacion <= 0:
                    p.poblacion = 0
                    p.activa = False
            mensaje = f"Peste en {imp.nombre}: poblacion reducida 10%"
        elif tipo == 'cosecha':
            bonus = random.randint(100, 300)
            imp.oro += bonus
            mensaje = f"Buena cosecha en {imp.nombre}: +{bonus} oro"
        elif tipo == 'tesoro':
            bonus = random.randint(100, 500)
            imp.oro += bonus
            mensaje = f"Tesoro encontrado en {imp.nombre}: +{bonus} oro"
        else:  # terremoto
            for p in self.provincias_de(imp.nombre):
                p.poblacion = int(p.poblacion * 0.95)
                p.felicidad = Sat(p.felicidad - 10)
                if p.poblacion <= 0:
                    p.poblacion = 0
                    p.activa = False
            mensaje = f"Terremoto en {imp.nombre}: danos severos"
        
        self.log_historial.append(mensaje)
        return mensaje

    def ejecutar_turnos(self, num=5):
        """Ejecuta multiples turnos de forma segura"""
        resultados = []
        for i in range(num):
            # Ejecutar un turno individual
            r, ia = self.procesar_fin_de_turno()
            resultados.append({
                'turno': self.turno_actual,
                'resumen': r,
                'ia': ia
            })
        return resultados

    # ==========================================
    # METRICAS DE RENDIMIENTO
    # ==========================================

    def calcular_ise(self, nombre_imperio):
        """Indice de Sostenibilidad Economica"""
        imp = self.obtener_imperio(nombre_imperio)
        if not imp or imp.turnos_totales == 0:
            return 0.0
        return imp.turnos_flujo_positivo / imp.turnos_totales

    def calcular_tmh(self, nombre_imperio):
        """Tiempo Medio en Estado de Huelga (turnos)"""
        provincias = self.provincias_de(nombre_imperio)
        if not provincias:
            return 0.0
        total_huelga = sum(p.turnos_huelga for p in provincias)
        return total_huelga / len(provincias)

    def calcular_tec(self, nombre_imperio):
        """Tasa de Eficiencia de Conquista"""
        imp = self.obtener_imperio(nombre_imperio)
        if not imp or imp.bajas_recibidas == 0:
            return imp.provincias_anexadas if imp.provincias_anexadas > 0 else 0.0
        return imp.provincias_anexadas / max(1, imp.bajas_recibidas / 100)

    def get_metricas(self, nombre_imperio):
        """Obtiene todas las metricas de un imperio"""
        return {
            'ise': self.calcular_ise(nombre_imperio),
            'tmh': self.calcular_tmh(nombre_imperio),
            'tec': self.calcular_tec(nombre_imperio),
            'turnos': self.turno_actual,
            'provincias': len(self.provincias_de(nombre_imperio)),
            'oro': self.obtener_imperio(nombre_imperio).oro if self.obtener_imperio(nombre_imperio) else 0
        }

    def get_estado_global(self):
        return {
            'turno': self.turno_actual,
            'imperios': {n: {
                'oro': i.oro, 
                'protectorado': i.es_protectorado, 
                'rey': i.rey_vivo,
                'provincias': len(self.provincias_de(n))
            } for n, i in self.imperios.items()}
        }

    # ==========================================
    # MODO CONSOLA - INTERFAZ DE USUARIO
    # ==========================================

    def ejecutar_consola(self):
        """Bucle principal para modo consola"""
        while True:
            try:
                comando = input("\n> ").strip().lower()
                if not comando:
                    continue
                    
                if comando == 'q':
                    print("Saliendo del simulador...")
                    break
                elif comando == 't':
                    self._ejecutar_turno_consola()
                elif comando == '5':
                    self._ejecutar_5_turnos_consola()
                elif comando == 's':
                    self._mostrar_estado_consola()
                elif comando == 'm':
                    self._mostrar_metricas_consola()
                elif comando == 'ia':
                    self._ejecutar_ia_consola()
                elif comando.startswith('r '):
                    self._reclutar_consola(comando)
                elif comando.startswith('f '):
                    self._fiesta_consola(comando)
                elif comando.startswith('i '):
                    self._impuestos_consola(comando)
                elif comando.startswith('a '):
                    self._atacar_consola(comando)
                else:
                    print("Comando no reconocido. Escribe 'h' para ayuda.")
                    
            except KeyboardInterrupt:
                print("\nSaliendo...")
                break
            except Exception as e:
                print(f"Error: {e}")

    def _ejecutar_turno_consola(self):
        """Ejecuta un turno en consola"""
        r, ia = self.procesar_fin_de_turno()
        print(f"\n--- TURNO {self.turno_actual} COMPLETADO ---")
        for nombre, data in r.items():
            print(f"{nombre}: +{data['ingresos']:.1f}o -{data['mantenimiento']:.1f}o = {data['oro']:.1f}o (Fel: {data['felicidad_promedio']:.1f}%)")
        for msg in ia:
            print(f"  IA: {msg}")

    def _ejecutar_5_turnos_consola(self):
        """Ejecuta 5 turnos en consola"""
        print("Ejecutando 5 turnos...")
        for i in range(5):
            r, ia = self.procesar_fin_de_turno()
            print(f"  Turno {self.turno_actual} completado")
        print("5 turnos completados")

    def _mostrar_estado_consola(self):
        """Muestra el estado en consola"""
        print(f"\n=== ESTADO DEL JUEGO - TURNO {self.turno_actual} ===")
        for nombre, imp in self.imperios.items():
            prov = self.provincias_de(nombre)
            print(f"\n{nombre}:")
            print(f"  Oro: {imp.oro:.1f}")
            print(f"  Estado: {'Protectorado' if imp.es_protectorado else 'Libre'}")
            print(f"  Rey: {'Vivo' if imp.rey_vivo else 'Muerto'}")
            print(f"  Provincias: {len(prov)}")
            if prov:
                for p in prov:
                    print(f"    - {p}")

    def _mostrar_metricas_consola(self):
        """Muestra metricas en consola"""
        print(f"\n=== METRICAS DE RENDIMIENTO - TURNO {self.turno_actual} ===")
        for nombre, imp in self.imperios.items():
            metricas = self.get_metricas(nombre)
            print(f"\n{nombre}:")
            print(f"  ISE (Sostenibilidad): {metricas['ise']:.2f}")
            print(f"  TMH (Huelga): {metricas['tmh']:.1f} turnos")
            print(f"  TEC (Conquista): {metricas['tec']:.2f}")
            print(f"  Provincias: {metricas['provincias']}")
            print(f"  Oro: {metricas['oro']:.1f}")

    def _ejecutar_ia_consola(self):
        """Ejecuta IA en consola"""
        print("Ejecutando IA enemiga...")
        resultados = self.procesar_ia_turno()
        for r in resultados:
            print(f"  {r}")

    def _reclutar_consola(self, comando):
        """Recluta tropas desde consola"""
        partes = comando.split()
        if len(partes) < 3:
            print("Uso: r <provincia> <cantidad>")
            return
        try:
            provincia = partes[1]
            cantidad = int(partes[2])
            r = self.reclutar_tropas(provincia, cantidad)
            if r['success']:
                print(f"Reclutados {cantidad} soldados en {provincia}")
            else:
                print(f"Error: {r['error']}")
        except ValueError:
            print("Cantidad debe ser un numero")

    def _fiesta_consola(self, comando):
        """Organiza fiesta desde consola"""
        partes = comando.split()
        if len(partes) < 2:
            print("Uso: f <provincia>")
            return
        provincia = partes[1]
        r = self.organizar_fiesta(provincia)
        if r['success']:
            print(f"Fiesta en {provincia}: felicidad {r['nueva_felicidad']:.1f}%")
        else:
            print(f"Error: {r['error']}")

    def _impuestos_consola(self, comando):
        """Cambia impuestos desde consola"""
        partes = comando.split()
        if len(partes) < 3:
            print("Uso: i <imperio> <tasa>")
            return
        try:
            imperio = partes[1]
            tasa = float(partes[2])
            r = self.cambiar_impuestos(imperio, tasa)
            if r['success']:
                print(f"Impuestos de {imperio}: {r['antigua_tasa']:.2f} -> {r['nueva_tasa']:.2f}")
            else:
                print(f"Error: {r['error']}")
        except ValueError:
            print("Tasa debe ser un numero")

    def _atacar_consola(self, comando):
        """Ataca desde consola"""
        partes = comando.split()
        if len(partes) < 4:
            print("Uso: a <origen> <destino> <tropas> [rey=s/n]")
            return
        try:
            origen = partes[1]
            destino = partes[2]
            tropas = int(partes[3])
            rey = len(partes) > 4 and partes[4].lower() == 's'
            r = self.atacar_provincia(origen, destino, tropas, rey)
            if r['success']:
                if r.get('victoria', False):
                    print(f"VICTORIA: Conquistaste {destino}!")
                elif r.get('rey_muerto', False):
                    print(f"MUERTE DEL REY: {self.imperio_jugador} es protectorado")
                else:
                    print(f"Derrota en {destino}")
            else:
                print(f"Error: {r['error']}")
        except ValueError:
            print("Tropas debe ser un numero")


# ==========================================
# MODO INTERFAZ GRAFICA (GUI)
# ==========================================

class ModoGUI:
    """Clase contenedora para el modo GUI - solo se importa PyQt si es necesario"""
    
    @staticmethod
    def ejecutar(motor):
        """Ejecuta la interfaz grafica"""
        try:
            from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                        QLabel, QPushButton, QComboBox, QTextEdit, QFrame,
                                        QMessageBox, QInputDialog, QApplication, QAction,
                                        QGridLayout)
            from PyQt5.QtCore import Qt, QTimer, pyqtSignal
            from PyQt5.QtGui import (QPainter, QColor, QBrush, QPen, QFont, 
                                    QLinearGradient, QPalette, QTextCursor)
            
            # ==========================================
            # WIDGET DEL MAPA
            # ==========================================
            
            class MapaWidget(QWidget):
                def __init__(self, motor, parent=None):
                    super().__init__(parent)
                    self.motor = motor
                    self.setMinimumSize(500, 350)
                    self.setStyleSheet("background-color: #1a252f;")
                    
                    self.colores = {
                        'Imperio Romano': (46, 204, 113),
                        'Tribus Galas': (231, 76, 60),
                        'Egipcios': (241, 196, 15),
                        'Griegos': (52, 152, 219)
                    }
                    
                    self.animacion = 0
                    self.timer_anim = QTimer()
                    self.timer_anim.timeout.connect(self._animar)
                    self.timer_anim.start(100)
                    
                def _animar(self):
                    self.animacion = (self.animacion + 1) % 360
                    self.update()
                    
                def paintEvent(self, event):
                    painter = QPainter(self)
                    painter.setRenderHint(QPainter.Antialiasing)
                    
                    w, h = self.width(), self.height()
                    provincias = [p for p in self.motor.mapa.values() if p.activa]
                    
                    if not provincias:
                        painter.drawText(w//2 - 50, h//2, "No hay provincias activas")
                        return
                        
                    num = len(provincias)
                    cx, cy = w//2, h//2
                    radius = min(w, h)//2 - 40
                    
                    gradient = QLinearGradient(0, 0, w, h)
                    gradient.setColorAt(0, QColor(26, 37, 47))
                    gradient.setColorAt(1, QColor(44, 62, 80))
                    painter.fillRect(0, 0, w, h, QBrush(gradient))
                    
                    for i, prov in enumerate(provincias):
                        angle = (2 * 3.14159 * i) / num + math.radians(self.animacion * 0.1)
                        x = cx + radius * 0.7 * math.cos(angle)
                        y = cy + radius * 0.7 * math.sin(angle)
                        
                        color = self.colores.get(prov.propietario, (155, 155, 155))
                        r, g, b = color
                        
                        size = max(18, min(50, int(prov.poblacion / 200)))
                        if prov.es_capital:
                            size = int(size * 1.2)
                            painter.setPen(QPen(QColor(255, 215, 0), 3))
                        else:
                            painter.setPen(QPen(QColor(255, 255, 255), 2))
                        
                        if prov.felicidad > 80:
                            painter.setBrush(QBrush(QColor(r, g, b, 200)))
                            for j in range(3):
                                s = size + j * 3
                                painter.setBrush(QBrush(QColor(r, g, b, 50 - j * 15)))
                                painter.drawEllipse(int(x - s//2), int(y - s//2), s, s)
                        
                        painter.setBrush(QBrush(QColor(r, g, b)))
                        painter.drawEllipse(int(x - size//2), int(y - size//2), size, size)
                        
                        painter.setPen(QPen(QColor(255, 255, 255), 1))
                        font = QFont("Arial", 7)
                        painter.setFont(font)
                        
                        painter.drawText(int(x - 18), int(y + size//2 + 15), prov.nombre[:8])
                        painter.drawText(int(x - 10), int(y + 2), f"⚔{prov.tropas}")
                        
                        if prov.felicidad < 30:
                            painter.setPen(QPen(QColor(255, 0, 0), 2))
                            painter.drawText(int(x - 5), int(y - size//2 - 5), "!")
                        elif prov.felicidad > 80:
                            painter.setPen(QPen(QColor(0, 255, 0), 2))
                            painter.drawText(int(x - 5), int(y - size//2 - 5), "+")
                        
                        if prov.es_capital:
                            painter.setPen(QPen(QColor(255, 215, 0), 2))
                            painter.drawText(int(x - 6), int(y - size//2 - 5), "*")
                    
                    x, y = w - 180, 10
                    painter.fillRect(x - 8, y - 8, 175, len(self.motor.imperios) * 24 + 30, 
                                    QColor(0, 0, 0, 200))
                    painter.setPen(QPen(QColor(255, 255, 255), 1))
                    font = QFont("Arial", 9, QFont.Bold)
                    painter.setFont(font)
                    painter.drawText(x, y + 14, " LEYENDA")
                    y += 20
                    
                    font = QFont("Arial", 8)
                    painter.setFont(font)
                    for nombre, imp in self.motor.imperios.items():
                        color = self.colores.get(nombre, (155, 155, 155))
                        painter.setBrush(QBrush(QColor(*color)))
                        painter.setPen(QPen(QColor(255, 255, 255), 1))
                        painter.drawRect(x, y, 14, 14)
                        painter.setPen(QPen(QColor(255, 255, 255), 1))
                        estado = "K" if imp.rey_vivo else "D"
                        ia = "AI" if imp.es_ia else "PL"
                        painter.drawText(x + 18, y + 11, f"{nombre[:10]} {ia} {estado} {imp.oro:.0f}o")
                        y += 20

            # ==========================================
            # PANEL DE INFORMACION
            # ==========================================
            
            class PanelInfo(QWidget):
                def __init__(self, motor, parent=None):
                    super().__init__(parent)
                    self.motor = motor
                    self.initUI()
                    
                def initUI(self):
                    layout = QVBoxLayout()
                    layout.setSpacing(3)
                    
                    titulo = QLabel("INFORMACION")
                    titulo.setStyleSheet("font-size: 13px; font-weight: bold; color: #ecf0f1; padding: 3px;")
                    layout.addWidget(titulo)
                    
                    self.labels = {}
                    for item in ['Oro', 'Impuestos', 'Estado', 'Rey', 'Provincias', 'Puntos', 'ISE', 'TMH', 'TEC']:
                        frame = QFrame()
                        frame.setStyleSheet("background-color: #34495e; border-radius: 3px;")
                        frame_layout = QHBoxLayout()
                        frame_layout.setContentsMargins(5, 2, 5, 2)
                        
                        label = QLabel(f"{item}:")
                        label.setStyleSheet("color: #bdc3c7; font-size: 10px; font-weight: bold;")
                        
                        value = QLabel("-")
                        value.setStyleSheet("color: #ecf0f1; font-size: 10px;")
                        value.setAlignment(Qt.AlignRight)
                        
                        frame_layout.addWidget(label)
                        frame_layout.addWidget(value)
                        frame.setLayout(frame_layout)
                        self.labels[item] = value
                        layout.addWidget(frame)
                    
                    line = QFrame()
                    line.setFrameShape(QFrame.HLine)
                    line.setStyleSheet("background-color: #34495e;")
                    layout.addWidget(line)
                    
                    titulo2 = QLabel("ESTADISTICAS")
                    titulo2.setStyleSheet("font-size: 11px; font-weight: bold; color: #ecf0f1; padding: 3px;")
                    layout.addWidget(titulo2)
                    
                    self.stats = QTextEdit()
                    self.stats.setStyleSheet("background-color: #34495e; color: #ecf0f1; border: none; border-radius: 3px; padding: 3px; font-size: 9px;")
                    self.stats.setReadOnly(True)
                    self.stats.setMaximumHeight(80)
                    layout.addWidget(self.stats)
                    
                    self.metricas_label = QLabel("")
                    self.metricas_label.setStyleSheet("color: #3498db; font-size: 9px; padding: 3px;")
                    self.metricas_label.setWordWrap(True)
                    layout.addWidget(self.metricas_label)
                    
                    layout.addStretch()
                    self.setLayout(layout)
                    self.setStyleSheet("background-color: #2c3e50;")
                    
                    self.timer = QTimer()
                    self.timer.timeout.connect(self.actualizar_auto)
                    self.timer.start(2000)
                    
                def actualizar(self, nombre):
                    imp = self.motor.obtener_imperio(nombre)
                    if not imp:
                        return
                        
                    self.labels['Oro'].setText(f"{imp.oro:.1f}")
                    self.labels['Impuestos'].setText(f"{imp.tasa_impuestos:.2f}x")
                    self.labels['Estado'].setText("Protectorado" if imp.es_protectorado else "Libre")
                    self.labels['Rey'].setText("Vivo" if imp.rey_vivo else "Muerto")
                    
                    prov = self.motor.provincias_de(nombre)
                    self.labels['Provincias'].setText(str(len(prov)))
                    self.labels['Puntos'].setText(f"{imp.puntos_movimiento}/{imp.puntos_movimiento_max}")
                    
                    metricas = self.motor.get_metricas(nombre)
                    self.labels['ISE'].setText(f"{metricas['ise']:.2f}")
                    self.labels['TMH'].setText(f"{metricas['tmh']:.1f}")
                    self.labels['TEC'].setText(f"{metricas['tec']:.2f}")
                    
                    if prov:
                        stats = f"Pob: {sum(p.poblacion for p in prov):,}\nTropas: {sum(p.tropas for p in prov)}\nFel: {sum(p.felicidad for p in prov)/len(prov):.1f}%"
                    else:
                        stats = "Sin provincias activas"
                    self.stats.setText(stats)
                    
                    self.metricas_label.setText(f"ISE: {metricas['ise']:.2f} | TMH: {metricas['tmh']:.1f} | TEC: {metricas['tec']:.2f}")
                    
                def actualizar_auto(self):
                    if hasattr(self.motor, 'imperio_jugador'):
                        self.actualizar(self.motor.imperio_jugador)

            # ==========================================
            # PANEL DE ACCIONES
            # ==========================================
            
            class PanelAcciones(QWidget):
                action_triggered = pyqtSignal(str, dict)
                
                def __init__(self, motor, parent=None):
                    super().__init__(parent)
                    self.motor = motor
                    self.parent_ventana = parent
                    self.initUI()
                    
                def initUI(self):
                    layout = QVBoxLayout()
                    layout.setSpacing(3)
                    
                    titulo = QLabel("ACCIONES")
                    titulo.setStyleSheet("font-size: 13px; font-weight: bold; color: #ecf0f1; padding: 3px;")
                    layout.addWidget(titulo)
                    
                    grid = QGridLayout()
                    grid.setSpacing(4)
                    
                    acciones = [
                        ("Reclutar", self.reclutar, "#2ecc71"),
                        ("Atacar", self.atacar, "#e74c3c"),
                        ("Fiesta", self.fiesta, "#f1c40f"),
                        ("Ver", self.ver_estado, "#3498db"),
                        ("Turno", self.turno, "#e67e22"),
                        ("5T", self.auto_turnos, "#9b59b6"),
                        ("Metricas", self.ver_metricas, "#1abc9c"),
                        ("IA", self.ejecutar_ia, "#8e44ad")
                    ]
                    
                    for i, (texto, func, color) in enumerate(acciones):
                        btn = QPushButton(texto)
                        btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: {color};
                                color: {'black' if color in ['#f1c40f', '#e67e22', '#1abc9c'] else 'white'};
                                border: none;
                                padding: 6px;
                                border-radius: 3px;
                                font-size: 10px;
                                font-weight: bold;
                            }}
                            QPushButton:hover {{ opacity: 0.8; }}
                            QPushButton:pressed {{ opacity: 0.6; }}
                        """)
                        btn.clicked.connect(func)
                        grid.addWidget(btn, i//2, i%2)
                        
                    layout.addLayout(grid)
                    
                    self.log_text = QTextEdit()
                    self.log_text.setStyleSheet("background-color: #34495e; color: #bdc3c7; border: none; border-radius: 3px; padding: 3px; font-size: 9px;")
                    self.log_text.setReadOnly(True)
                    self.log_text.setMaximumHeight(80)
                    layout.addWidget(self.log_text)
                    
                    layout.addStretch()
                    self.setLayout(layout)
                    self.setStyleSheet("background-color: #2c3e50;")
                    
                def log(self, msg):
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    self.log_text.append(f"[{timestamp}] {msg}")
                    if self.log_text.document().lineCount() > 50:
                        cursor = self.log_text.textCursor()
                        cursor.movePosition(QTextCursor.Start)
                        cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 10)
                        cursor.removeSelectedText()
                    
                def reclutar(self):
                    provincias = [p.nombre for p in self.motor.mapa.values() 
                                 if p.propietario == self.motor.imperio_jugador and p.activa]
                    if not provincias:
                        QMessageBox.warning(self, "Error", "No tienes provincias activas!")
                        return
                    provincia, ok = QInputDialog.getItem(self, "Reclutar", "Provincia:", provincias, 0, False)
                    if not ok:
                        return
                    cantidad, ok = QInputDialog.getInt(self, "Reclutar", "Cantidad:", 10, 1, 1000)
                    if ok:
                        r = self.motor.reclutar_tropas(provincia, cantidad)
                        if r['success']:
                            self.log(f"Reclutados {cantidad} soldados en {provincia}")
                            QMessageBox.information(self, "Exito", f"Reclutados {cantidad} soldados")
                        else:
                            self.log(f"Error: {r['error']}")
                            QMessageBox.warning(self, "Error", r['error'])
                        self.parent_ventana.actualizar_ui()
                        
                def atacar(self):
                    origenes = [p.nombre for p in self.motor.mapa.values() 
                               if p.propietario == self.motor.imperio_jugador and p.activa]
                    if not origenes:
                        QMessageBox.warning(self, "Error", "No tienes provincias activas!")
                        return
                    origen, ok = QInputDialog.getItem(self, "Atacar", "Origen:", origenes, 0, False)
                    if not ok:
                        return
                    destinos = [p.nombre for p in self.motor.mapa.values() 
                               if p.propietario != self.motor.imperio_jugador and p.activa]
                    if not destinos:
                        QMessageBox.warning(self, "Error", "No hay enemigos!")
                        return
                    destino, ok = QInputDialog.getItem(self, "Atacar", "Destino:", destinos, 0, False)
                    if not ok:
                        return
                    cantidad, ok = QInputDialog.getInt(self, "Atacar", "Tropas:", 10, 1, 1000)
                    if not ok:
                        return
                    rey = QMessageBox.question(self, "Rey", "Lidera el Rey?", 
                                              QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes
                    r = self.motor.atacar_provincia(origen, destino, cantidad, rey)
                    if r['success']:
                        if r.get('victoria', False):
                            self.log(f"VICTORIA: Conquistaste {destino}!")
                            QMessageBox.information(self, "Victoria!", f"Conquistaste {destino}!")
                        elif r.get('rey_muerto', False):
                            self.log(f"MUERTE DEL REY: {self.motor.imperio_jugador} es protectorado")
                            QMessageBox.warning(self, "Catastrofe!", "El Rey ha muerto en combate!")
                        else:
                            self.log(f"Derrota en {destino}")
                            QMessageBox.warning(self, "Derrota", f"Fuiste rechazado en {destino}")
                    else:
                        self.log(f"Error: {r.get('error', 'Error desconocido')}")
                        QMessageBox.warning(self, "Error", r.get('error', 'Error'))
                    self.parent_ventana.actualizar_ui()
                    
                def fiesta(self):
                    provincias = [p.nombre for p in self.motor.mapa.values() 
                                 if p.propietario == self.motor.imperio_jugador and p.activa]
                    if not provincias:
                        QMessageBox.warning(self, "Error", "No tienes provincias activas!")
                        return
                    provincia, ok = QInputDialog.getItem(self, "Fiesta", "Provincia:", provincias, 0, False)
                    if ok:
                        r = self.motor.organizar_fiesta(provincia)
                        if r['success']:
                            self.log(f"Fiesta en {provincia}: felicidad {r['nueva_felicidad']:.1f}%")
                            QMessageBox.information(self, "Fiesta", f"Felicidad: {r['nueva_felicidad']:.1f}%")
                        else:
                            self.log(f"Error: {r['error']}")
                            QMessageBox.warning(self, "Error", r['error'])
                        self.parent_ventana.actualizar_ui()
                        
                def ver_estado(self):
                    self.parent_ventana.mostrar_estado()
                    
                def ver_metricas(self):
                    self.parent_ventana.mostrar_metricas()
                    
                def ejecutar_ia(self):
                    self.log("Ejecutando IA enemiga...")
                    resultados = self.motor.procesar_ia_turno()
                    for r in resultados:
                        self.log(f"IA: {r}")
                    self.parent_ventana.actualizar_ui()
                    QMessageBox.information(self, "IA", f"IA ejecutada para {len(resultados)} imperios")
                    
                def turno(self):
                    r, ia = self.motor.procesar_fin_de_turno()
                    self.log(f"Turno {self.motor.turno_actual} completado")
                    for nombre, data in r.items():
                        self.log(f"   {nombre}: +{data['ingresos']}o -{data['mantenimiento']}o = {data['oro']}o")
                    for msg in ia:
                        self.log(f"IA: {msg}")
                    self.parent_ventana.actualizar_ui()
                    QMessageBox.information(self, "Turno", f"Turno {self.motor.turno_actual} completado")
                    
                def auto_turnos(self):
                    self.log("Ejecutando 5 turnos...")
                    self.motor.ejecutar_turnos(5)
                    self.log("5 turnos completados")
                    self.parent_ventana.actualizar_ui()
                    QMessageBox.information(self, "Simulacion", "5 turnos completados")

            # ==========================================
            # VENTANA PRINCIPAL
            # ==========================================
            
            class VentanaPrincipal(QMainWindow):
                def __init__(self, motor):
                    super().__init__()
                    self.motor = motor
                    self.tutorial_mostrado = False
                    self.initUI()
                    
                def initUI(self):
                    self.setWindowTitle("Age of Conquest IV - Simulador GUI v5.0")
                    self.setGeometry(100, 100, 1200, 700)
                    self.setStyleSheet("""
                        QMainWindow { background-color: #1a252f; }
                        QToolTip { background-color: #2c3e50; color: #ecf0f1; border: 1px solid #3498db; }
                    """)
                    
                    central = QWidget()
                    self.setCentralWidget(central)
                    layout = QHBoxLayout()
                    layout.setContentsMargins(0, 0, 0, 0)
                    central.setLayout(layout)
                    
                    self.mapa = MapaWidget(self.motor)
                    layout.addWidget(self.mapa, 3)
                    
                    panel_derecho = QWidget()
                    panel_derecho.setMaximumWidth(320)
                    layout_derecho = QVBoxLayout()
                    layout_derecho.setContentsMargins(0, 0, 0, 0)
                    panel_derecho.setLayout(layout_derecho)
                    
                    self.selector = QComboBox()
                    self.selector.addItems(self.motor.imperios.keys())
                    self.selector.setCurrentText(self.motor.imperio_jugador)
                    self.selector.currentTextChanged.connect(self.cambiar_imperio)
                    self.selector.setStyleSheet("""
                        QComboBox {
                            background-color: #34495e;
                            color: #ecf0f1;
                            padding: 5px;
                            border: 2px solid #3498db;
                            border-radius: 3px;
                            font-size: 12px;
                        }
                        QComboBox QAbstractItemView {
                            background-color: #34495e;
                            color: #ecf0f1;
                            selection-background-color: #3498db;
                        }
                    """)
                    layout_derecho.addWidget(self.selector)
                    
                    self.panel_info = PanelInfo(self.motor, self)
                    layout_derecho.addWidget(self.panel_info, 2)
                    
                    self.panel_acciones = PanelAcciones(self.motor, self)
                    layout_derecho.addWidget(self.panel_acciones, 1)
                    
                    layout.addWidget(panel_derecho, 1)
                    
                    self.statusBar().showMessage("Bienvenido a Age of Conquest IV v2.0")
                    self.statusBar().setStyleSheet("background-color: #2c3e50; color: #ecf0f1;")
                    
                    self.crear_menu()
                    self.actualizar_ui()
                    
                    QTimer.singleShot(500, self.mostrar_tutorial)
                    
                def crear_menu(self):
                    menubar = self.menuBar()
                    menubar.setStyleSheet("background-color: #2c3e50; color: #ecf0f1;")
                    
                    archivo = menubar.addMenu('Archivo')
                    salir = QAction('Salir', self)
                    salir.setShortcut('Ctrl+Q')
                    salir.triggered.connect(self.close)
                    archivo.addAction(salir)
                    
                    ayuda = menubar.addMenu('Ayuda')
                    tutorial = QAction('Tutorial', self)
                    tutorial.triggered.connect(self.mostrar_tutorial)
                    ayuda.addAction(tutorial)
                    
                    about = QAction('Acerca de', self)
                    about.triggered.connect(self.mostrar_acerca)
                    ayuda.addAction(about)
                    
                def cambiar_imperio(self, nombre):
                    self.motor.imperio_jugador = nombre
                    self.actualizar_ui()
                    
                def actualizar_ui(self):
                    self.mapa.update()
                    self.panel_info.actualizar(self.motor.imperio_jugador)
                    imp = self.motor.obtener_imperio(self.motor.imperio_jugador)
                    if imp:
                        self.statusBar().showMessage(f"Turno {self.motor.turno_actual} | {self.motor.imperio_jugador} | Oro: {imp.oro:.1f}")
                    
                def mostrar_estado(self):
                    estado = f"TURNO {self.motor.turno_actual}\n\n"
                    for n, i in self.motor.imperios.items():
                        prov = self.motor.provincias_de(n)
                        estado += f"{n}: {i.oro:.1f} oro | {'Protectorado' if i.es_protectorado else 'Libre'} | Rey: {'Vivo' if i.rey_vivo else 'Muerto'} | {len(prov)} provincias\n"
                    estado += "\nPROVINCIAS ACTIVAS:\n"
                    for n, p in self.motor.mapa.items():
                        if p.activa:
                            estado += f"  {p}\n"
                    estado += f"\nTotal provincias: {len([p for p in self.motor.mapa.values() if p.activa])}"
                    QMessageBox.information(self, "Estado del Juego", estado)
                    
                def mostrar_metricas(self):
                    texto = "METRICAS DE RENDIMIENTO\n"
                    texto += "=" * 40 + "\n\n"
                    
                    for nombre, imp in self.motor.imperios.items():
                        metricas = self.motor.get_metricas(nombre)
                        texto += f"{nombre}\n"
                        texto += f"   ISE (Sostenibilidad): {metricas['ise']:.2f}\n"
                        texto += f"   TMH (Huelga): {metricas['tmh']:.1f} turnos\n"
                        texto += f"   TEC (Conquista): {metricas['tec']:.2f}\n"
                        texto += f"   Provincias: {metricas['provincias']}\n"
                        texto += f"   Oro: {metricas['oro']:.1f}\n\n"
                    
                    texto += "=" * 40 + "\n"
                    texto += f"Turno actual: {self.motor.turno_actual}\n"
                    
                    QMessageBox.information(self, "Metricas de Rendimiento", texto)
                    
                def mostrar_tutorial(self):
                    if self.tutorial_mostrado:
                        return
                    self.tutorial_mostrado = True
                    
                    tutorial_text = """
                    <h1>Bienvenido a Age of Conquest IV</h1>
                    <p><b>Simulador de Estrategia - UNET</b></p>
                    <hr>
                    
                    <h2>TUTORIAL RAPIDO</h2>
                    
                    <h3>IMPERIOS</h3>
                    <ul>
                        <li><b>Imperio Romano</b> (Jugador) - Tu controlas este imperio</li>
                        <li><b>Tribus Galas</b> (IA) - Controlado por Inteligencia Artificial</li>
                        <li><b>Egipcios</b> (IA) - Controlado por Inteligencia Artificial</li>
                        <li><b>Griegos</b> (IA) - Controlado por Inteligencia Artificial</li>
                    </ul>
                    
                    <h3>ACCIONES DISPONIBLES</h3>
                    <ul>
                        <li><b>Reclutar</b> - Convierte poblacion y oro en soldados</li>
                        <li><b>Atacar</b> - Conquista provincias enemigas</li>
                        <li><b>Fiesta</b> - Aumenta la felicidad (costo: 50 oro)</li>
                        <li><b>Turno</b> - Avanza un turno</li>
                        <li><b>5T</b> - Avanza 5 turnos automaticamente</li>
                        <li><b>IA</b> - Ejecuta acciones de la IA manualmente</li>
                    </ul>
                    
                    <h3>METRICAS DE RENDIMIENTO</h3>
                    <ul>
                        <li><b>ISE</b> - Indice de Sostenibilidad Economica (0-1)</li>
                        <li><b>TMH</b> - Tiempo Medio en Huelga (turnos)</li>
                        <li><b>TEC</b> - Tasa de Eficiencia de Conquista</li>
                    </ul>
                    
                    <h3>CONSEJOS</h3>
                    <ul>
                        <li>Manten la felicidad > 50% para recaudar impuestos</li>
                        <li>Los impuestos altos generan mas oro pero reducen la felicidad</li>
                        <li>Tasa de impuestos = 0 da bonificacion de +10 de felicidad</li>
                        <li>El Rey en batalla da +25% de dano</li>
                        <li>Si el Rey muere, el imperio se vuelve protectorado</li>
                    </ul>
                    
                    <hr>
                    <p><b>Integrantes:</b> Bryant Vivas, Angel Sanchez, Leynner Angulo</p>
                    <p><b>Agosto 2026</b></p>
                    """
                    
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Tutorial - Age of Conquest IV")
                    msg.setText(tutorial_text)
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.setIcon(QMessageBox.Information)
                    msg.exec_()
                    
                def mostrar_acerca(self):
                    QMessageBox.about(self, "Acerca de",
                                      """
                                      <h1>Age of Conquest IV</h1>
                                      <p><b>Simulador de Estrategia v2.0</b></p>
                                      <hr>
                                      <p><b>Curso:</b> Simulacion de Sistemas</p>
                                      <p><b>Universidad:</b> UNET</p>
                                      <p><b>Agosto 2026</b></p>
                                      <hr>
                                      <p><b>Integrantes:</b></p>
                                      <ul>
                                          <li>Bryant Vivas</li>
                                          <li>Angel Sanchez</li>
                                          <li>Leynner Angulo</li>
                                      </ul>
                                      <hr>
                                      <p><b>Caracteristicas:</b></p>
                                      <ul>
                                          <li>Modelo economico completo</li>
                                          <li>Batallas Lanchester estocasticas</li>
                                          <li>Inteligencia Artificial enemiga</li>
                                          <li>Metricas de rendimiento (ISE, TMH, TEC)</li>
                                          <li>Lista de Eventos Futuros (LEF)</li>
                                          <li>Tutorial interactivo</li>
                                      </ul>
                                      """)

            # Ejecutar GUI
            app = QApplication(sys.argv)
            app.setStyle('Fusion')
            
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(26, 37, 47))
            palette.setColor(QPalette.WindowText, QColor(236, 240, 241))
            palette.setColor(QPalette.Base, QColor(44, 62, 80))
            palette.setColor(QPalette.AlternateBase, QColor(52, 73, 94))
            palette.setColor(QPalette.ToolTipBase, QColor(44, 62, 80))
            palette.setColor(QPalette.ToolTipText, QColor(236, 240, 241))
            palette.setColor(QPalette.Text, QColor(236, 240, 241))
            palette.setColor(QPalette.Button, QColor(52, 73, 94))
            palette.setColor(QPalette.ButtonText, QColor(236, 240, 241))
            palette.setColor(QPalette.BrightText, QColor(255, 215, 0))
            app.setPalette(palette)
            
            ventana = VentanaPrincipal(motor)
            ventana.show()
            
            sys.exit(app.exec_())
            
        except ImportError as e:
            print("ERROR: No se pudo importar PyQt5.")
            print("Instala con: pip install PyQt5")
            print(f"Detalle: {e}")
            sys.exit(1)


# ==========================================
# MAIN - SELECCION DE MODO
# ==========================================

def main():
    """Punto de entrada principal - selecciona modo consola o GUI"""
    
    # Verificar si se pasó argumento por línea de comandos
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ['-c', '--console', 'consola']:
            modo = 'consola'
        elif sys.argv[1].lower() in ['-g', '--gui', 'grafica']:
            modo = 'gui'
        else:
            modo = None
    else:
        modo = None
    
    # Si no hay argumento, mostrar selector
    if modo is None:
        print("=" * 50)
        print("  AGE OF CONQUEST IV - SIMULADOR")
        print("=" * 50)
        print("\nSelecciona el modo de ejecucion:")
        print("  1. Interfaz Grafica (GUI)")
        print("  2. Consola (Texto)")
        print("\n  O usa argumentos:")
        print("    python main_simple.py -g   # Modo grafico")
        print("    python main_simple.py -c   # Modo consola")
        print("=" * 50)
        
        while True:
            try:
                opcion = input("\nElige (1/2): ").strip()
                if opcion == '1':
                    modo = 'gui'
                    break
                elif opcion == '2':
                    modo = 'consola'
                    break
                else:
                    print("Opcion no valida. Elige 1 o 2.")
            except KeyboardInterrupt:
                print("\nSaliendo...")
                return
    
    # Crear motor de simulacion
    motor = MotorSimulacion(modo_consola=(modo == 'consola'))
    
    # Ejecutar en el modo seleccionado
    if modo == 'consola':
        motor.ejecutar_consola()
    else:
        ModoGUI.ejecutar(motor)


if __name__ == "__main__":
    main()