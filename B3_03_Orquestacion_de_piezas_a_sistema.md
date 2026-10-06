<!-- Slide number: 1 -->

De piezas
a sistema

La orquestación: cómo las piezas corren juntas
Énfasis II · Producción 4.0
Ingeniería Industrial
Universidad
de Medellín

Ciencia y Libertad

<!-- Slide number: 2 -->
UdeM
Ingeniería Industrial · Producción 4.0
Dónde estamos

E2 · ARQUITECTURA
SUS SKILLS
HOY
el plano
✓ entregado
los ladrillos
✓ montados
se pega

Tienen el plano y tienen los ladrillos.
Lo que no tienen todavía es algo que corra.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 3 -->

1
Tener piezas no es
tener sistema

El diagnóstico de dónde están hoy — y por qué no alcanza

<!-- Slide number: 4 -->
UdeM
Ingeniería Industrial · Producción 4.0
Una skill sola no se dispara

Una skill solo corre cuando alguien la invoca, con el dato correcto,
en el momento correcto.
Hoy, ese alguien son ustedes:

skill ABC
USTEDES
skill ROP
USTEDES
skill BOM
clasifica
copian y
pegan
calcula
copian y
pegan
proyecta

Eso no es un sistema. Es un humano haciendo de pegamento entre las piezas.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 5 -->
UdeM
Ingeniería Industrial · Producción 4.0
Por qué eso no alcanza

No es un problema de estética: es un problema de ingeniería

Falla
Qué significa en la operación

No es reproducible
Si lo corren dos veces, puede salir distinto. Dependió de qué pegaron y en qué orden.

No escala
Funciona con un material. Con trescientos, no hay humano que aguante.

No se puede medir
Si cada corrida es distinta, no hay línea base ni mejora que comparar.

No se puede demostrar
Nadie puede operarlo sin ustedes dos al lado.

Un proceso que depende de una persona específica para correr es, exactamente,
un cuello de botella.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 6 -->

2
Las cuatro capas,
ahora con el «cómo»

Su propia arquitectura de E2, aterrizada a piezas que existen

<!-- Slide number: 7 -->
UdeM
Ingeniería Industrial · Producción 4.0
Su arquitectura ya tenía las capas

Lo que faltaba era decir con qué se construye cada una

INTERACCIÓN
lo que el usuario ve y decide · tablero · aprobación

ORQUESTACIÓN
quién llama a quién y en qué orden  ◄── lo de hoy

LÓGICA
un componente por responsabilidad · fórmulas + IA

DATOS
el estado · la base
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 8 -->
UdeM
Ingeniería Industrial · Producción 4.0
Con qué se construye cada capa

Capa
Qué hace
Con qué

Datos
El estado. La única fuente de verdad
La base de datos que ya montaron

Lógica
Un componente por responsabilidad
Fórmula si el resultado es calculable;
modelo si hay que interpretar

Orquestación
Llama los componentes en orden,
maneja fallos y para cuando toca
Código propio — hoy decidimos cómo

Interacción
Dispara, muestra y aprueba
Una aplicación con un botón

Regla de oro: cada capa solo habla con la de al lado. Si la interfaz consulta la base
directo, se saltó la lógica — y nadie sabe qué pasó.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 9 -->

3
El contrato
de cada pieza

Qué recibe, qué entrega. El error más silencioso del curso

<!-- Slide number: 10 -->
UdeM
Ingeniería Industrial · Producción 4.0
Toda pieza tiene un contrato

Dos preguntas que toda pieza debe responder antes de escribirse:

¿QUÉ RECIBE?
¿QUÉ ENTREGA?
qué datos necesita
para poder trabajar
qué devuelve,
y en qué forma

Si no puede responder las dos, no es una pieza: es una intención.

En términos de Ingeniería Industrial
Es la especificación de la entrega entre dos estaciones de un proceso:
qué llega, en qué estado, y con qué se recibe. Ya lo saben hacer en planta.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 11 -->
UdeM
Ingeniería Industrial · Producción 4.0
El error silencioso

La falla número uno — y no da ningún mensaje de error

NO SE PUEDE ENCADENAR
SÍ SE PUEDE ENCADENAR
«El punto de reorden de la
lámina es de unas 450
unidades aproximadamente,
aunque conviene revisarlo.»
sku: MP-LAM-CR-1200
rop: 450
stock_seguridad: 118
unidad: lámina
Las dos dicen lo mismo. Solo una sirve para que el paso siguiente trabaje sin un humano
que la interprete.

Una pieza que devuelve párrafo no se encadena. Tiene que devolver dato.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 12 -->
UdeM
Ingeniería Industrial · Producción 4.0
Cómo probar que el contrato sirve

Una sola pregunta, y es fácil de aplicar:

¿Puede el paso siguiente usar esta salida sin que un humano la lea e interprete?

Respuesta
Qué significa

Sí
El contrato está bien. Pueden encadenar.

No
No es un contrato todavía. Hay que definir qué devuelve y en qué forma.
Apliquen esta pregunta a cada skill que montaron. Es la tarea de hoy, y es donde van
a encontrar lo que falta.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 13 -->

4
De la skill
al módulo

El ejemplo completo: qué escribieron, y en qué se convierte

<!-- Slide number: 14 -->
UdeM
Ingeniería Industrial · Producción 4.0
Primero: qué es un módulo

Un módulo es un archivo con una función adentro.
Y una función es una máquina:

ENTRA ALGO
HACE UNA COSA
SALE ALGO

En términos de Ingeniería Industrial
Es una estación de la línea. El misterio estaba en el nombre, no en la cosa.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 15 -->
UdeM
Ingeniería Industrial · Producción 4.0
Paso 1 · La skill que ya escribieron

Un procedimiento, en palabras

•  Está en palabras.
•  Dice los pasos, en orden.
•  Dice cómo verificar el resultado.
•  Todavía nadie la puede ejecutar.
SKILL  ·  clasificar ABC

Cuando usarla:
   asignar politica diferenciada

Pasos:
   1. traer consumo anual y costo
   2. valor = consumo x costo
   3. ordenar de mayor a menor
   4. acumular el porcentaje
   5. cortar en 80% y 95%

Verificacion:
   las tres clases suman el 100%

Esto ya lo tienen hecho. Es la parte difícil.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 16 -->
UdeM
Ingeniería Industrial · Producción 4.0
Paso 2 · El módulo que sale de ella

El mismo procedimiento, en instrucciones que la máquina sigue

•  La primera línea dice qué RECIBE.
•  La última dice qué ENTREGA.
•  El medio son los pasos de la skill, uno por uno.
•  No lo tienen que inventar: ya lo escribieron.
# nucleo/abc

def clasificar_abc(materiales):

    for m in materiales:                 # 2
        m.valor = m.consumo * m.costo

    ordenar(materiales, por=valor)       # 3

    acum = 0
    for m in materiales:                 # 4 y 5
        acum += m.valor
        m.clase = clase_segun(acum)

    return materiales

No hay traducción creativa. El módulo es la skill, escrita para que corra.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 17 -->
UdeM
Ingeniería Industrial · Producción 4.0
El contrato son dos líneas

Y son las únicas que le importan al resto del sistema

def clasificar_abc( materiales ):        <-- RECIBE
        ...
    return materiales                    <-- ENTREGA

RECIBE
ENTREGA
una lista de materiales,
cada uno con sku,
consumo y costo
la misma lista, cada uno
ahora con valor
y clase

Lo que importa no es solo QUÉ entrega: es en QUÉ FORMA lo entrega.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 18 -->
UdeM
Ingeniería Industrial · Producción 4.0
Esto ya lo saben hacer

Con otro nombre

ESTACIÓN 3
LA FICHA DE ENTREGA
ESTACIÓN 4

termina su parte
qué llega, en qué estado,
en qué cantidad
recibe y sigue

El contrato es esa ficha. Si la estación 3 entrega algo que la 4 no esperaba,
la línea para.

En términos de Ingeniería Industrial
Especificar la entrega entre dos estaciones es trabajo de ingeniero industrial.
Aquí es exactamente lo mismo — solo que las estaciones son archivos.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 19 -->
UdeM
Ingeniería Industrial · Producción 4.0
Por qué el contrato se define ANTES

CONTRATOS PRIMERO
MÓDULOS PRIMERO
Deciden qué recibe y qué
entrega cada pieza.

Cada módulo se escribe
una vez. Y encajan.
Escriben, y al conectar
descubren que el 3 entrega
algo que el 4 no puede usar.

Reescriben los dos.

Definir el contrato cuesta cinco minutos.
Descubrir que no encaja cuesta dos módulos.
Por eso el trazado de la tarea de hoy va en papel, antes de tocar el teclado.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 20 -->
UdeM
Ingeniería Industrial · Producción 4.0
Hay tres tipos de módulo

Y el orquestador no distingue entre ellos

Tipo
Qué hace
Ejemplo

Fórmula
Calcula un resultado exacto
ROP, EOQ, ABC, explosión de BOM

IA
Interpreta lo sucio o redacta
normalizar categorías, explicar una propuesta

Datos
Lee y escribe en la base
traer el estado, guardar la propuesta

Los tres tienen la misma forma de contrato: reciben algo, entregan algo.
Desde afuera, un módulo de IA se ve idéntico a una fórmula.
Eso es lo que hace que se puedan cambiar sin romper el resto.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 21 -->
UdeM
Ingeniería Industrial · Producción 4.0
Y así se conecta todo

El orquestador: siete líneas

materiales = datos.leer_materiales()
materiales = normalizador.limpiar(materiales)        <-- IA
clases     = abc.clasificar_abc(materiales)
leads      = lead_time.calcular(ordenes)
rops       = rop.calcular(clases, leads)
propuestas = politica.comparar(stock, rops)
datos.guardar(propuestas)

Lo que sale de una línea entra en la siguiente.
Ahí se ve por qué los contratos tienen que encajar.
El orquestador no calcula nada. Solo llama, en orden, y pasa el resultado.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 22 -->

5
Las tres formas
de orquestar

Quién decide el orden de los pasos — y cuánto cuesta cada opción

<!-- Slide number: 23 -->
UdeM
Ingeniería Industrial · Producción 4.0
Forma 1 · Secuencia fija

El orden lo decidió el ingeniero, de antemano

1. Leer
2. Normalizar
3. Calcular
4. Comparar
5. Proponer
traer el estado
limpiar lo sucio
las fórmulas
contra la política
y registrar

Secuencia fija

A favor
Siempre corre igual. Barata. Auditable: se sabe exactamente qué pasó y en qué orden.

En contra
No se adapta. Si aparece un caso que no estaba previsto, no sabe qué hacer con él.

Cuándo
Cuando el proceso ya se conoce y se repite igual.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 24 -->
UdeM
Ingeniería Industrial · Producción 4.0
Forma 2 · El modelo decide

Un agente escoge qué pieza llamar, según la situación

AGENTE
decide el camino

Leer
Normalizar
Calcular
Conciliar

Agente que decide

A favor
Maneja lo que no estaba previsto. Útil donde hay ambigüedad real.

En contra
Puede escoger distinto la próxima vez. Más caro de correr y mucho más difícil de verificar.

Cuándo
Solo donde el orden genuinamente no se puede saber de antemano.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 25 -->
UdeM
Ingeniería Industrial · Producción 4.0
Forma 3 · Mixta

La que se usa en la realidad

1. Leer
2. Normalizar
3. Calcular
¿excepción?
5. Proponer

AGENTE / HUMANO
solo para el caso raro

Secuencia fija para el camino conocido.
Criterio — del modelo o de una persona — solo en las bifurcaciones.
Barata y auditable donde se puede; flexible solo donde hace falta.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 26 -->
UdeM
Ingeniería Industrial · Producción 4.0
La regla para elegir

Si ya sabes el orden del proceso,
no le pagues a un modelo para que lo adivine.
Es la misma lección del curso, aplicada al flujo en vez de al número:

Qué se decide
Con qué

El número
Una fórmula. Nunca un modelo.

El orden de los pasos
Código, si el proceso se conoce. Un agente solo si no.

El dato sucio y la explicación
Ahí sí, el modelo. Es donde se gana su lugar.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 27 -->
UdeM
Ingeniería Industrial · Producción 4.0
Y en su caso, ¿cuál va?

La pregunta que tienen que contestar ustedes, con argumento
Mírenlo así: el orden de los pasos de su operación, ¿lo pueden escribir hoy
en una hoja, sin ambigüedad?

Su respuesta
Qué implica

Sí, lo puedo escribir
Entonces va secuencia fija. Un agente ahí sería gasto sin beneficio.

Depende del caso
Mixta. Fija para el camino conocido, criterio en la bifurcación.

No, cambia siempre
Agente. Pero tienen que poder justificar por qué cambia.

En la sustentación les van a preguntar por qué escogieron una y no otra.
«Porque sí» no es una respuesta de arquitectura.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 28 -->

6
Dónde vive
la verdad

El estado del sistema: qué se guarda, y dónde

<!-- Slide number: 29 -->
UdeM
Ingeniería Industrial · Producción 4.0
La base manda. El chat solo transporta.

MAL
BIEN
•  El resultado queda en la conversación.
•  Se cierra la ventana y se perdió.
•  Nadie puede auditar qué se decidió.
•  Cada paso lee de la base.
•  Cada paso escribe a la base.
•  Queda el registro de qué se decidió y cuándo.

Si un resultado solo existe en la conversación, muere con la conversación.

En términos de Ingeniería Industrial
Es la diferencia entre un proceso con registros
y un proceso que vive en la cabeza de alguien.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 30 -->
UdeM
Ingeniería Industrial · Producción 4.0
Y además les resuelve la trazabilidad

Que es requisito de E4, no un extra
Si cada corrida deja registro en la base, de regalo pueden responder:
•  ¿Qué propuso el sistema el martes pasado, y por qué?
•  ¿Cuántas propuestas aprobó el planeador y cuántas rechazó?
•  ¿Mejoró el indicador desde que el sistema está corriendo?
•  ¿Cuánto costó operarlo?

Sin registro no hay medición. Y sin medición no hay E4 ni caso de negocio.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 31 -->

7
Criterio de parada
y supervisión

La cajita del diagrama se vuelve una condición de verdad

<!-- Slide number: 32 -->
UdeM
Ingeniería Industrial · Producción 4.0
El flujo tiene que detenerse en algún lado

En su arquitectura de E2, «aprobación humana» era una caja. Hoy deja de ser caja:

EL SISTEMA
SE DETIENE
UNA PERSONA

propone qué pedir
y por qué
y espera
aprueba o rechaza

Ningún sistema de este curso compromete dinero sin que una persona lo apruebe.
Y la decisión del humano también se registra. Esa es la evidencia de que la supervisión
existe de verdad y no solo en el diagrama.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 33 -->
UdeM
Ingeniería Industrial · Producción 4.0
¿Cuándo debe detenerse?

El criterio lo define el ingeniero, no el modelo

Disparador
Qué pasó
Para qué sirve

Monto alto
El valor de lo que propone pasa de un umbral
Protege la plata

Dato faltante
Le falta información para decidir bien
Evita decidir a ciegas

Inconsistencia
Dos fuentes dicen cosas distintas
Evita propagar un error

Caso nuevo
Se topa con algo que no estaba previsto
Evita inventar

Cada umbral es una decisión de ingeniería que hay que poder defender con un número.
«Para cuando el monto pasa de X» exige saber por qué X y no otro.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 34 -->
UdeM
Ingeniería Industrial · Producción 4.0
Los dos errores de calibración

PARAR EN TODO
NO PARAR NUNCA
Si pregunta en cada paso,
no automatizaron nada:
hicieron un formulario
más lento que el Excel.
Si nunca pregunta,
comprometieron dinero
sin control — y el primer
error lo paga el cliente.

El punto medio no se adivina: se calibra. Empiecen conservadores y vayan soltando
a medida que el sistema demuestre que acierta.
Eso también es un hallazgo defendible en la sustentación.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 35 -->

8
Cómo se materializa

De la teoría a algo que abre, corre y se puede mostrar

<!-- Slide number: 36 -->
UdeM
Ingeniería Industrial · Producción 4.0
Dos caminos para montar la orquestación

Aplicación local propia
Orquestador externo

Procesos que mantener vivos
1 · solo su aplicación
2 · la app y el orquestador

Dónde vive el flujo
En el repositorio, versionado
En la base interna de la herramienta

Depurar un fallo
Un solo lugar donde mirar
¿Falló el orquestador o el paso?

La interfaz de control
Es la misma aplicación
Un formulario limitado

Qué hay que aprender
Lo que ya están usando
Una herramienta más

Pesa más de lo que parece: si el flujo no está en el repositorio,
la pieza central del sistema queda fuera de la evidencia de trabajo del equipo.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 37 -->
UdeM
Ingeniería Industrial · Producción 4.0
Vamos con la aplicación local

•  Un solo proyecto, un solo lenguaje, un solo sitio donde buscar cuando algo falle.
•  Todo queda en el repositorio: el flujo es código y el código tiene historial.
•  Corre en su propio equipo. Sin nube, sin cuentas nuevas, sin depender de internet.
•  Es a la vez el prototipo que corre en E3 y el tablero de control de E5 — el mismo artefacto, madurado.
•  Para mostrarlo: se abre, se oprime un botón, corre. Eso es una demostración.

No es la única arquitectura válida. Es la que mejor cabe en el tiempo que queda
y la que menos piezas tiene que puedan fallar el día de la sustentación.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 38 -->
UdeM
Ingeniería Industrial · Producción 4.0
Qué tipo de aplicación es

Concretamente, para que no quede en el aire

Qué tipo de aplicación

NO es
una app de celular

NO es
un sitio en internet

NO es
algo que haya que pagar ni publicar

SÍ es
una página en el navegador, servida desde su propio equipo

Corren un comando, se abre el navegador en su propia máquina.
Cierran el comando y se apaga. No hay nada que administrar.
Para la sustentación: se abre, se oprime un botón, corre. Eso es la demostración.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 39 -->
UdeM
Ingeniería Industrial · Producción 4.0
Cómo se ve el tablero

Reposición de inventario

Nivel de servicio
Exactitud de inventario
Propuestas de hoy
—
—
—

Correr reposición

Material
Cantidad
Por qué
Decisión

material A
—
bajo el punto de reorden
aprobar / rechazar

material B
—
descuadre: se detuvo y pregunta
aprobar / rechazar

material C
—
cambio de mix en el plan
aprobar / rechazar

Un botón que dispara, una tabla que explica, y una decisión humana por fila.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 40 -->
UdeM
Ingeniería Industrial · Producción 4.0
Y el tablero se escribe en pocas líneas

•  Cada línea produce un elemento en la página.
•  No hay que escribir diseño web.
•  El tablero no calcula: solo muestra y recoge la decisión.
titulo("Reposicion de inventario")

si boton("Correr reposicion"):
    propuestas = orquestador.correr()
    tabla(propuestas)

    si boton("Aprobar"):
        datos.aprobar(propuestas)

Por eso es viable: la interfaz de control no es un proyecto aparte.
Son unas líneas encima del orquestador que ya tienen.
Y esa misma página es el entregable de la interfaz de E5.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 41 -->
UdeM
Ingeniería Industrial · Producción 4.0
Cómo se organiza el proyecto

•  Un archivo por responsabilidad.
•  El orquestador no calcula nada: solo llama y pasa el resultado.
•  El tablero no calcula nada: solo muestra y recoge la aprobación.
•  Cada pieza se puede probar sola.
proyecto/
  app              ← el tablero · el botón · la aprobación
  orquestador      ← la secuencia: llama los pasos en orden
  nucleo/
      datos        ← leer y escribir en la base
      formula_1    ← FÓRMULA
      formula_2    ← FÓRMULA
      formula_3    ← FÓRMULA
      conciliador  ← IA + regla
      normalizador ← IA
  skills/          ← la especificación de cada módulo

Si un archivo hace dos cosas, son dos archivos.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 42 -->
UdeM
Ingeniería Industrial · Producción 4.0
Y sus skills, ¿para qué quedaron?

Para lo más importante

LA SKILL
EL MÓDULO
el procedimiento
escrito
el procedimiento
montado

Uno a uno: cada skill que montaron se convierte en un módulo del núcleo.
La carpeta de skills se queda — es la especificación de lo que el módulo debe hacer.

En términos de Ingeniería Industrial
Es el documento del procedimiento contra la línea que lo ejecuta.
Ninguno reemplaza al otro: sin el documento, nadie sabe si la línea quedó bien.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 43 -->
UdeM
Ingeniería Industrial · Producción 4.0
La proporción es la tesis del curso

Cuenten los módulos del núcleo:

FÓRMULA
IA
la mayoría
dos: lo sucio
y la explicación

Esa proporción no es una limitación de presupuesto: es la respuesta correcta.
Si la IA calcula el número, usaron la herramienta equivocada.
Y de paso: con el modelo haciendo solo dos cosas, el costo de operar cabe en nada.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 44 -->
UdeM
Ingeniería Industrial · Producción 4.0
Cómo entra la IA, exactamente

Un módulo más — con el mismo contrato

•  Recibe algo, entrega algo. Igual que una fórmula.
•  El orquestador no sabe que adentro hay un modelo.
•  El modelo nunca ve el problema completo: recibe una tarea pequeña.
# nucleo/normalizador

CATEGORIAS = ["Lamina", "Tuberia", ...]

def limpiar_categoria(texto_sucio):
    r = modelo.preguntar(
        "Normaliza a una de la lista.
         Responde solo la categoria.",
        lista=CATEGORIAS,
        texto=texto_sucio)
    return r

Desde afuera es un módulo cualquiera. Por eso se puede cambiar por una regla
el día que descubran que una regla alcanza.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 45 -->
UdeM
Ingeniería Industrial · Producción 4.0
Y el módulo que llama al modelo es el que lo verifica

•  Si el modelo devuelve algo que no está en la lista, el módulo lo rechaza.
•  Y en vez de inventar, se detiene y pregunta.
def limpiar_categoria(texto_sucio):
    r = modelo.preguntar(...)

    si r no esta en CATEGORIAS:
        return DETENER(
            "categoria no reconocida")

    return r

La defensa contra la alucinación vive en el código del módulo,
no en la instrucción que se le da al modelo.
Confiar en que el modelo obedezca no es una defensa. Verificar sí.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 46 -->
UdeM
Ingeniería Industrial · Producción 4.0
Cómo se ve una corrida completa

De una sola acción hasta donde debe detenerse

1
2
3
4
5
Alguien oprime
el botón

Lee el estado
de la base

Normaliza
lo sucio

Corren las
fórmulas

Compara contra
la política

6
7
8
9

Arma la
propuesta
¿Excepción?
SE DETIENE
Una persona
aprueba
Registra todo
en la base

Una acción al principio, una decisión humana en el medio, un registro al final.
Eso es un sistema.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 47 -->
UdeM
Ingeniería Industrial · Producción 4.0
La tarea para el miércoles

Dos cosas. Son pocas a propósito.

1 · EL TRAZADO
2 · EL ESQUELETO
Impriman su diagrama de E2.
Para cada flecha: ¿qué skill
la implementa?

Marquen con rojo las flechas
que no tienen nada detrás.
Esas son el hueco.

En papel. Veinte minutos.
El proyecto con la estructura
de carpetas, la aplicación
abriendo, y UN módulo de
fórmula que lea de la base.

Escriban PRIMERO su contrato:
qué recibe y qué entrega.

Y que el número lo puedan
verificar a mano.

Si el miércoles ya hay una fórmula leyendo de la base y dando un número correcto,
el resto de la cadena es repetir lo mismo. Ese es todo el truco.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 48 -->
UdeM
Ingeniería Industrial · Producción 4.0
Cómo saben que van bien

•  Pueden decir qué recibe y qué entrega cada pieza, sin dudar.
•  Ninguna pieza devuelve párrafo donde el paso siguiente necesita un dato.
•  El resultado de cada paso queda en la base, no en una conversación.
•  Pueden decir en qué punto el sistema se detiene y por qué ahí.
•  Pueden justificar por qué escogieron secuencia fija, agente o mixta.
•  Ninguna fórmula quedó en manos del modelo.

Si pueden responder las seis, la arquitectura dejó de ser un dibujo.
Énfasis II · Producción 4.0
Orquestación

<!-- Slide number: 49 -->

Las piezas no son el sistema.
El sistema es el orden
en que corren.

Producción 4.0 · Universidad de Medellín