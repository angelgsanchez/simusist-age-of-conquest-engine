import random
import math
import sys

# ==========================================
# FUNCIONES AUXILIARES MATEMÁTICAS
# ==========================================
def Sat(x):
    """Función de saturación para mantener variables en el espacio topológico [0, 100]."""
    return max(0.0, min(100.0, x))

# ==========================================
# CLASES DE ESTADO (STOCKS)
# ==========================================
class Provincia:
    def __init__(self, nombre, propietario, poblacion, tropas, felicidad=100.0):
        self.nombre = nombre
        self.propietario = propietario
        self.poblacion = poblacion
        self.tropas = tropas
        self.felicidad = felicidad # Hit: Nivel de Felicidad [0, 100]

class Imperio:
    def __init__(self, nombre, oro_inicial, tasa_impuestos):
        self.nombre = nombre
        self.oro = oro_inicial
        self.tasa_impuestos = tasa_impuestos
        self.es_protectorado = False

# ==========================================
# MOTOR DE SIMULACIÓN
# ==========================================
class MotorAgeOfConquest:
    def __init__(self):
        self.turno_actual = 1
        self.imperios = {}
        self.mapa = {}
        
        # Parámetros Fijos (Constantes del Juego)
        self.alfa = 0.05        # Coeficiente de Capacidad Tributaria Per Cápita
        self.M_div = 20.0       # Divisor Logístico Operacional
        self.delta = 8.0        # Coeficiente de Shock Bélico
        self.gamma = 10.0       # Coeficiente de Amortiguación Social (Fiestas)
        self.delta_Hrey = 20.0  # Penalización por Anarquía Institucional
        self.p_muerte = 0.25    # Probabilidad de Muerte del Líder
        self.H_huelga = 50.0    # Umbral Crítico de Ruptura Fiscal

    def registrar_imperio(self, imperio):
        self.imperios[imperio.nombre] = imperio

    def registrar_provincia(self, provincia):
        self.mapa[provincia.nombre] = provincia

    def reclutar_tropas(self, nombre_provincia, cantidad):
        """Flujo de Alta Militar"""
        prov = self.mapa.get(nombre_provincia)
        if not prov:
            print("[ERROR] Provincia no encontrada.")
            return

        imperio = self.imperios[prov.propietario]
        costo = cantidad * 2.0  # Costo fijo hipotético por tropa
        
        if imperio.oro >= costo and prov.poblacion > cantidad:
            imperio.oro -= costo
            prov.poblacion -= cantidad
            prov.tropas += cantidad
            print(f"[ÉXITO] Se reclutaron {cantidad} soldados en {prov.nombre}. Costo: {costo} oro.")
        else:
            print("[ERROR] Oro o población insuficiente.")

    def organizar_fiesta(self, nombre_provincia):
        """Tasa de Inversión Social voluntaria"""
        prov = self.mapa.get(nombre_provincia)
        imperio = self.imperios[prov.propietario]
        costo_fiesta = 50.0
        
        if imperio.oro >= costo_fiesta:
            imperio.oro -= costo_fiesta
            prov.felicidad = Sat(prov.felicidad + self.gamma)
            print(f"[INVERSIÓN SOCIAL] Fiesta celebrada en {prov.nombre}. Felicidad actual: {prov.felicidad}%.")
        else:
            print("[ERROR] Oro insuficiente para organizar fiestas.")

    def resolver_conflicto(self, prov_origen, prov_destino, tropas_atacantes, rey_presente):
        """Resolución de combate mediante Lanchester Estocástico"""
        origen = self.mapa.get(prov_origen)
        destino = self.mapa.get(prov_destino)
        
        if not origen or not destino:
            print("[ERROR] Provincia(s) inválida(s).")
            return
            
        imperio_atacante = self.imperios[origen.propietario]
        
        if origen.tropas < tropas_atacantes:
            print("[ERROR LOGÍSTICO] Tropas insuficientes en la provincia de origen.")
            return

        print(f"\n>>> INICIANDO CAMPAÑA MILITAR <<<")
        print(f"Atacante: {origen.propietario} desde {origen.nombre}")
        print(f"Defensor: {destino.propietario} en {destino.nombre}")
        
        origen.tropas -= tropas_atacantes
        A_k = float(tropas_atacantes)
        D_k = float(destino.tropas)
        
        mu_rey = 1.25 if rey_presente else 1.00
        eficacia_A = 0.10
        eficacia_D = 0.10
        k = 0
        
        while A_k > 0 and D_k > 0:
            k += 1
            X_A = random.uniform(0.7, 1.3)
            X_D = random.uniform(0.7, 1.3)
            
            delta_A_k = D_k * eficacia_D * X_D
            delta_D_k = A_k * eficacia_A * mu_rey * 1.0 * X_A # mu_terreno = 1.0
            
            A_k = max(0.0, A_k - delta_A_k)
            D_k = max(0.0, D_k - delta_D_k)
            
        A_k = int(A_k)
        D_k = int(D_k)
        
        if A_k > 0:
            print(f"[VICTORIA] ¡{origen.propietario} conquista {destino.nombre} en {k} asaltos! Sobreviven {A_k} tropas.")
            destino.propietario = origen.propietario
            destino.tropas = A_k
        else:
            print(f"[DERROTA] {destino.propietario} repele el ataque tras {k} asaltos. Sobreviven {D_k} tropas.")
            destino.tropas = D_k
            origen.felicidad = Sat(origen.felicidad - self.delta)
            print(f"[-] Shock Bélico: La felicidad en {origen.nombre} cae a {origen.felicidad:.1f}%.")
            
            if rey_presente:
                Z = 1 if random.random() <= self.p_muerte else 0 
                if Z == 1:
                    print(f"[CRÍTICO] ¡El Rey de {origen.propietario} ha caído en combate!")
                    imperio_atacante.es_protectorado = True 
                    origen.felicidad = Sat(origen.felicidad - self.delta_Hrey) 
                    print(f"[ANARQUÍA] {origen.propietario} es ahora un Protectorado. Moral desplomada.")

    def procesar_fin_de_turno(self):
        """Ciclo de Resolución de Fin de Turno (Demografía, Economía y Limites)"""
        print(f"\n{'='*40}")
        print(f" PROCESANDO FIN DE TURNO {self.turno_actual} ")
        print(f"{'='*40}")
        
        for nombre_imp, imperio in self.imperios.items():
            provincias_propias = [p for p in self.mapa.values() if p.propietario == nombre_imp]
            ingresos_brutos = 0.0
            costo_mantenimiento = 0.0
            
            for prov in provincias_propias:
                # 1. EVOLUCIÓN AMBIENTAL Y MORAL
                if imperio.tasa_impuestos > 1.0:
                    prov.felicidad -= (imperio.tasa_impuestos * 15.0)
                elif imperio.tasa_impuestos == 0.0:
                    prov.felicidad += 10.0
                prov.felicidad = Sat(prov.felicidad)

                # 2. DINÁMICA DEMOGRÁFICA
                if prov.felicidad >= self.H_huelga:
                    prov.poblacion = int(prov.poblacion * 1.01) # Crecimiento 1%
                else:
                    prov.poblacion = int(prov.poblacion * 0.99) # Decrecimiento 1%
                
                # 3. FLUIDEZ MACROECONÓMICA
                if prov.felicidad >= self.H_huelga:
                    ingresos_brutos += (prov.poblacion * self.alfa) * imperio.tasa_impuestos
                else:
                    print(f"[ALERTA] Huelga fiscal en {prov.nombre} ({nombre_imp}). Recaudación nula.")
                
                # 4. LOGÍSTICA MILITAR
                costo_mantenimiento += max(1.0, math.floor(prov.tropas / self.M_div))

            # 5. REGULACIÓN COLONIAL (Vasallaje)
            pago_protectorado = 0.0
            if imperio.es_protectorado:
                pago_protectorado = ingresos_brutos * 0.10
                ingresos_brutos -= pago_protectorado
                print(f"[-] {nombre_imp} paga {pago_protectorado:.1f} oro como exacción colonial.")

            # 6. BALANCE FINAL DE LA TESORERÍA
            imperio.oro = imperio.oro + ingresos_brutos - costo_mantenimiento
            
            print(f"[{nombre_imp}] Ingresos: +{ingresos_brutos:.1f} | Mantenimiento: -{costo_mantenimiento:.1f} | Tesoro: {imperio.oro:.1f}")
            if imperio.oro < 0:
                print(f"[DÉFICIT FINANCIERO] {nombre_imp} se encuentra en quiebra y deudas.")
                
        self.turno_actual += 1

    def mostrar_estado(self):
        print(f"\n--- ESTADO GLOBAL (TURNO {self.turno_actual}) ---")
        for nombre, imp in self.imperios.items():
            estado_pol = "Protectorado" if imp.es_protectorado else "Libre"
            print(f"Imperio: {nombre} | Tesoro: {imp.oro:.1f} oro | Impuestos: {imp.tasa_impuestos}x | Estatus: {estado_pol}")
            
        print("\n--- TERRITORIOS ---")
        for nombre, prov in self.mapa.items():
            print(f"[{prov.nombre}] Prop: {prov.propietario} | Pob: {prov.poblacion} | Tropas: {prov.tropas} | Moral: {prov.felicidad:.1f}%")
        print("-----------------------------------")

# ==========================================
# INTERFAZ DE LÍNEA DE COMANDOS (CLI)
# ==========================================
def main():
    motor = MotorAgeOfConquest()
    
    # Configuración Inicial
    motor.registrar_imperio(Imperio("Imperio Romano", oro_inicial=500, tasa_impuestos=1.0))
    motor.registrar_imperio(Imperio("Tribus Galas", oro_inicial=200, tasa_impuestos=0.8))
    
    motor.registrar_provincia(Provincia("Roma", "Imperio Romano", poblacion=10000, tropas=200, felicidad=80.0))
    motor.registrar_provincia(Provincia("Galia", "Tribus Galas", poblacion=5000, tropas=150, felicidad=75.0))
    
    print("========================================")
    print(" MOTOR DE SIMULACIÓN AGE OF CONQUEST IV")
    print("========================================")
    
    # Bucle Principal Interactivo
    while True:
        motor.mostrar_estado()
        
        print("\n¿Qué acción deseas tomar este turno?")
        print("1. Reclutar Tropas")
        print("2. Atacar Provincia")
        print("3. Organizar Fiesta Popular (Mitigar Crisis)")
        print("4. Cambiar Tasa de Impuestos")
        print("5. Terminar Turno (Ejecutar LEF y Avanzar)")
        print("6. Salir del Simulador")
        
        opcion = input("\nIngresa el número de tu acción: ")
        
        if opcion == "1":
            prov = input("Nombre de tu provincia (ej. Roma): ")
            try:
                cant = int(input("Cantidad de soldados a reclutar: "))
                motor.reclutar_tropas(prov, cant)
            except ValueError:
                print("Cantidad inválida.")
                
        elif opcion == "2":
            origen = input("Provincia de Origen (tuya): ")
            destino = input("Provincia de Destino (enemiga): ")
            try:
                cant = int(input("Cantidad de soldados a enviar: "))
                rey = input("¿El Rey lidera la batalla? (s/n): ").lower() == 's'
                motor.resolver_conflicto(origen, destino, cant, rey)
            except ValueError:
                print("Cantidad inválida.")
                
        elif opcion == "3":
            prov = input("Nombre de la provincia a intervenir: ")
            motor.organizar_fiesta(prov)
            
        elif opcion == "4":
            imp = input("Nombre de tu imperio (ej. Imperio Romano): ")
            try:
                tasa = float(input("Nueva tasa (ej. 0.0 para cero, 1.5 para alta): "))
                if imp in motor.imperios:
                    motor.imperios[imp].tasa_impuestos = tasa
                    print(f"Impuestos de {imp} actualizados a {tasa}.")
                else:
                    print("Imperio no encontrado.")
            except ValueError:
                print("Tasa inválida. Usa formato decimal.")
                
        elif opcion == "5":
            motor.procesar_fin_de_turno()
            
        elif opcion == "6":
            print("Saliendo de la simulación. ¡Hasta pronto!")
            sys.exit()
            
        else:
            print("Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    main()
