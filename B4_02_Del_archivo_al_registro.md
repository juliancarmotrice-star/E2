<!-- Slide number: 1 -->

Del archivo
al registro

La ingesta de datos y la instrumentación
Énfasis II · Producción 4.0
Ingeniería Industrial
Universidad
de Medellín

Ciencia y Libertad

<!-- Slide number: 2 -->
UdeM
Ingeniería Industrial · Producción 4.0
Dónde están

CORRE
ESTÁ PROBADO
DA EL NÚMERO BIEN
✓
✓
✓
Falta una pregunta que todavía no se han hecho:

¿De dónde lee el sistema los datos?
Porque hoy los lee del archivo. Y ahí hay un problema de fondo.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 3 -->
UdeM
Ingeniería Industrial · Producción 4.0
El archivo no es el dato

Es el documento que trae el dato

EL ARCHIVO
LA BASE
es la remisión:
llega, se revisa, se asienta
es el kardex:
es el registro que manda

Nadie corre el inventario sobre el montón de remisiones que llegaron.
Las asienta en el kardex, y corre sobre el kardex.
Si el sistema lee el archivo en cada corrida, están operando sobre la pila de papeles.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 4 -->
UdeM
Ingeniería Industrial · Producción 4.0
Qué se rompe si el estado vive en el archivo

Qué falla
Qué significa en la operación

No hay historia
Cada corrida empieza de cero. El sistema tiene amnesia.

No hay medición
Si nada queda guardado, no hay antes ni después que comparar.

No hay trazabilidad
Nadie puede saber qué propuso el sistema la semana pasada, ni por qué.

Hay dos verdades
El archivo dice una cosa, el tablero otra, y nadie sabe cuál manda.

Un sistema sin registro no se puede mejorar, porque no se puede medir.
Y lo que no se mide, no se defiende.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 5 -->
UdeM
Ingeniería Industrial · Producción 4.0
Una carga de datos tiene cinco pasos

Y ninguno es opcional

1. ESCOGER
2. VALIDAR
3. NORMALIZAR
4. REPORTAR
5. ESCRIBIR
el usuario selecciona
el archivo
¿están las columnas?
¿los tipos cuadran?
categorías, unidades,
fechas
qué aceptó
y qué rechazó
a la base

El paso 3 es donde vive la IA: interpretar lo que viene escrito de cualquier forma.
El resto es determinístico.
Y de aquí en adelante, todos los módulos leen de la base.
Ninguno vuelve a tocar el archivo.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 6 -->
UdeM
Ingeniería Industrial · Producción 4.0
El paso 4: la carga tiene que rendir cuentas

2.362 filas leidas
2.347 cargadas
   15 rechazadas  ->  fecha invalida
•  Si la carga es silenciosa, nunca saben qué botó.
•  Un dato rechazado sin avisar es un dato perdido — y nadie se enteró.
•  Este reporte es lo primero que va a mirar alguien que audite el sistema.

Pruébenlo con sus propios datos: ahí hay fechas imposibles. ¿Su carga las reporta?
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 7 -->
UdeM
Ingeniería Industrial · Producción 4.0
Dos requisitos duros de la carga

Los dos se prueban en diez minutos

ACUMULATIVA
IDEMPOTENTE
Los datos nuevos se SUMAN
a los viejos. No los reemplazan.

Una operación real recibe
datos nuevos cada mes.
Si cada carga borra la anterior,
el sistema tiene amnesia.
Cargar el MISMO archivo dos
veces no duplica nada.

Alguien va a cargar dos veces.
Siempre pasa. El sistema tiene
que aguantarlo sin inventar
movimientos que no existieron.

Si la carga duplica, el inventario queda inflado — y todas las fórmulas
que vienen después dan mal. Con el número bien calculado.
Es el error más caro de este tipo de sistema, y el más fácil de pasar por alto.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 8 -->

TALLER EN CLASE
45 min
Construir la carga y probarla

Armen la pantalla de carga con los cinco pasos. Que escriba a la base, no a memoria.
1

Carguen un archivo. Anoten cuántas filas quedaron en la base.
2

Carguen EL MISMO archivo otra vez. Vuelvan a contar.
3

¿Subió el número? La carga duplica: está roto. Arréglenlo antes de seguir.
4

Ahora carguen un archivo con filas nuevas. ¿Se sumaron, o reemplazaron las viejas?
5

Pasa si: el conteo no cambia al recargar, los datos nuevos se suman, y el reporte dice qué rechazó.
Énfasis II · Producción 4.0

<!-- Slide number: 9 -->
UdeM
Ingeniería Industrial · Producción 4.0
Instrumentación: el sistema se mide solo

HASTA AHORA
DESDE AHORA
ustedes miden
el sistema
el sistema
se mide solo

Porque nadie va a hacer la prueba del papel todos los días.
Si medirlo depende de que ustedes estén, el sistema no está instrumentado.

En términos de Ingeniería Industrial
Una máquina sin instrumentos se opera a punta de intuición.
El tablero de la máquina no es un lujo: es cómo se sabe que está trabajando bien.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 10 -->
UdeM
Ingeniería Industrial · Producción 4.0
Qué debe medir de sí mismo

Dónde
Qué mide
Para qué sirve

De la carga
Filas leídas, cargadas y rechazadas
Calidad del dato que entra

De la corrida
Cuántas propuestas generó
Trabajo que ahorró

De las paradas
Cuántas veces se detuvo, y por qué
Si el criterio está bien calibrado

De la decisión
Cuántas aprobó y cuántas rechazó el humano
Si el sistema acierta

Del costo
Cuánto tardó la corrida
Costo de operación

Fíjense en la cuarta: si el humano rechaza casi todo lo que el sistema propone,
el sistema no sirve — y solo se sabe si quedó registrado.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 11 -->
UdeM
Ingeniería Industrial · Producción 4.0
Ya construyeron el primer instrumento

Sin darse cuenta

El reporte del paso 4 es instrumentación:
es el sistema rindiendo cuentas de sí mismo.
Lo que falta es hacer lo mismo con la corrida completa:
•  Cada corrida queda registrada, con su fecha.
•  Qué procesó, qué propuso, dónde se detuvo.
•  Qué decidió el humano en cada propuesta.

Una tabla más en la base: la bitácora de corridas.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 12 -->
UdeM
Ingeniería Industrial · Producción 4.0
Cómo saben que van bien

•  La carga reporta cuántas filas aceptó y cuántas rechazó, y por qué.
•  Cargar dos veces el mismo archivo no cambia nada.
•  Los datos nuevos se suman a los viejos, no los reemplazan.
•  Ningún módulo lee del archivo: todos leen de la base.
•  Cada corrida queda registrada con su fecha y su resultado.
•  Pueden decir cuántas veces el sistema se detuvo, y por qué.

Si pueden responder las seis, el sistema dejó de ser una calculadora bonita.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 13 -->

Un dato que no quedó
registrado no pasó.

Producción 4.0 · Universidad de Medellín