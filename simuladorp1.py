class Provincia:
    def __init__(self, nombre, propietario, poblacion, tropas):
        self.nombre = nombre
        self.propietario = propietario
        self.poblacion = poblacion
        self.tropas = tropas
        
    def crecimiento_poblacional(self, tasa=0.05):
        """Aumenta la población en cada turno."""
        self.poblacion = int(self.poblacion * (1 + tasa))

class Imperio:
    def __init__(self, nombre, oro_inicial, tasa_impuestos):
        self.nombre = nombre
        self.oro = oro_inicial
        self.tasa_impuestos = tasa_impuestos  # Porcentaje (ej. 0.15 = 15%)
        self.costo_mantenimiento_tropa = 1.0  # Oro por unidad en cada turno
        
class MotorAgeOfConquest:
    def __init__(self):
        self.turnos_transcurridos = 0
        self.imperios = {}
        self.mapa = {}

    def registrar_imperio(self, imperio):
        self.imperios[imperio.nombre] = imperio

    def registrar_provincia(self, provincia):
        self.mapa[provincia.nombre] = provincia

    def reclutar_tropas(self, nombre_imperio, nombre_provincia, cantidad):
        """Lógica de reclutamiento: cuesta oro y reduce la población."""
        imperio = self.imperios[nombre_imperio]
        provincia = self.mapa[nombre_provincia]
        costo_reclutamiento = 2.0  # Costo por tropa
        
        costo_total = cantidad * costo_reclutamiento
        
        if imperio.oro >= costo_total and provincia.poblacion > cantidad:
            imperio.oro -= costo_total
            provincia.poblacion -= cantidad
            provincia.tropas += cantidad
            print(f"[RECLUTAMIENTO] {cantidad} tropas reclutadas en {provincia.nombre}.")
        else:
            print("[ERROR] Oro o población insuficiente para reclutar.")

    def resolver_conflicto(self, prov_origen, prov_destino, tropas_atacantes):
        """Mecánica de resolución de conflictos (Ecuación determinista básica)."""
        origen = self.mapa[prov_origen]
        destino = self.mapa[prov_destino]
        
        if origen.tropas < tropas_atacantes:
            print("[ERROR] No hay suficientes tropas en la provincia de origen.")
            return

        print(f"[COMBATE] {origen.propietario} ataca {destino.nombre} ({destino.propietario}) con {tropas_atacantes} tropas.")
        origen.tropas -= tropas_atacantes
        
        # Ecuación de combate: El defensor tiene ventaja táctica (multiplicador 1.2)
        fuerza_defensiva = destino.tropas * 1.2
        fuerza_ofensiva = tropas_atacantes * 1.0
        
        if fuerza_ofensiva > fuerza_defensiva:
            # Gana el atacante
            bajas_atacante = int(destino.tropas * 0.8)
            tropas_sobrevivientes = tropas_atacantes - bajas_atacante
            print(f"[RESULTADO] ¡{origen.propietario} conquista {destino.nombre}! Sobreviven {tropas_sobrevivientes} tropas.")
            
            destino.propietario = origen.propietario
            destino.tropas = tropas_sobrevivientes
        else:
            # Gana el defensor
            bajas_defensor = int(tropas_atacantes * 0.5)
            destino.tropas -= bajas_defensor
            print(f"[RESULTADO] {destino.propietario} repele el ataque. Le quedan {destino.tropas} tropas.")

    def procesar_turno(self):
        """Calcula el estado del siguiente turno (Economía y Población)."""
        self.turnos_transcurridos += 1
        print(f"\n{'='*15} INICIANDO TURNO {self.turnos_transcurridos} {'='*15}")
        
        # 1. Economía y Mantenimiento
        for nombre, imperio in self.imperios.items():
            ingresos_totales = 0
            mantenimiento_total = 0
            
            provincias_propias = [p for p in self.mapa.values() if p.propietario == nombre]
            
            for prov in provincias_propias:
                # Ecuación de ingresos: Población * Tasa de Impuestos
                ingresos_totales += prov.poblacion * imperio.tasa_impuestos
                # Ecuación de gastos: Tropas * Costo de Mantenimiento
                mantenimiento_total += prov.tropas * imperio.costo_mantenimiento_tropa
                # Actualizar demografía
                prov.crecimiento_poblacional()
                
            balance_neto = ingresos_totales - mantenimiento_total
            imperio.oro += balance_neto
            
            print(f"[{nombre}] Ingresos: +{ingresos_totales:.1f} | Mantenimiento: -{mantenimiento_total:.1f} | Tesoro Actual: {imperio.oro:.1f}")
            
            # Penalización por bancarrota
            if imperio.oro < 0:
                print(f"[BANCARROTA] {nombre} no puede mantener su ejército. Tropas desertando...")
                for prov in provincias_propias:
                    prov.tropas = int(prov.tropas * 0.7) # Pierde el 30% de sus tropas

# ==========================================
# ÁREA DE PRUEBAS Y SIMULACIÓN (MAIN)
# ==========================================
if __name__ == "__main__":
    motor = MotorAgeOfConquest()
    
    # 1. Inicializar variables de entrada (Estado inicial)
    motor.registrar_imperio(Imperio("Roma", oro_inicial=100, tasa_impuestos=0.10))
    motor.registrar_imperio(Imperio("Cartago", oro_inicial=80, tasa_impuestos=0.15))
    
    motor.registrar_provincia(Provincia("Italia", "Roma", poblacion=1000, tropas=50))
    motor.registrar_provincia(Provincia("Galia", "Roma", poblacion=500, tropas=20))
    motor.registrar_provincia(Provincia("Norte de África", "Cartago", poblacion=1200, tropas=60))
    
    # 2. Acciones del jugador en el Turno 1
    motor.reclutar_tropas("Roma", "Italia", cantidad=10)
    motor.resolver_conflicto("Italia", "Norte de África", tropas_atacantes=40)
    
    # 3. Calcular estado del siguiente turno (Se ejecuta la lógica matemática)
    motor.procesar_turno()
