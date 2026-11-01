# Diario (con meditación diaria) — cómo actualizar

Esta carpeta genera la app **Diario** (la carpeta de arriba, repositorio `DiarioMeditacion`) a partir de la app **Epacta**
(carpeta «Diario app», que nunca se modifica) y de los ePub de meditaciones de la carpeta `medis` (aquí dentro; no se sube a GitHub).

## Cuándo ejecutarlo
- Cada vez que actualices la app Diario (después de `actualizar_diario.py`), para que la nueva app
  recoja la epacta, el Misal, los libros enlazados, etc.
- Si cambias o añades algún ePub de meditaciones.

## Cómo
En VSCode, abre esta carpeta y en el terminal:

    python generar.py

Rutas en `config.json` (relativas a esta carpeta): `diario` (app Diario), `medis` (ePub), `destino` (la app nueva).
Solo escribe los archivos que cambian, así Git sube pocos archivos.

## Qué añade a la app Diario
- Portada: botón **🙏 Meditación diaria** debajo de «Sagrada Escritura».
- Pantalla del día (`#/med`): celebración (de la epacta/Diario) y enlaces a todas las meditaciones posibles de
  los tres libros: fiesta del día, tiempo litúrgico (domingo con su ciclo A/B/C, feria…) y devociones
  (siete domingos de San José, octava del Corpus…). Flechas para otros días.
- **Libros**: dos libros nuevos con índice y búsqueda: *Meditaciones (7 tomos)*, *Siempre con Él* (9 tomos en uno)
  Además, «Hablar con Dios» es el libro que ya trae el Diario (con sus enlaces a la Biblia); la meditación diaria enlaza a sus meditaciones. Las notas a pie se abren tocando el número.
- En **todos** los libros: selecciona un texto y pulsa **🖍 Resaltar**. Tocar un resaltado permite quitarlo.
  Pantalla **Mis resaltados** (`#/resaltados`), por libro, con exportación a .md.

## Notas
- El calendario litúrgico se calcula para cualquier año (España: Epifanía el 6 de enero, Ascensión y Corpus en domingo)
  y se contrasta con el título del día del Misal/epacta. Se ha comprobado con los 220 días de 2026 que lo indican.
- «Aniversario de la elección del Papa» se asigna al 8 de mayo (León XIV). «Aniversario de la ordenación episcopal
  del Padre» no tiene fecha asignada: está en el índice del libro.

## María Valtorta
- El libro se genera desde `valtorta/Valtorta_La_vida_de_Jesus.epub` (aquí dentro; no se sube a GitHub).
- `valtorta_enlaces.json` guarda la correlación Evangelios–Valtorta por párrafo (915 enlaces: capítulo según las
  concordancias de la web de María Valtorta, párrafo localizado comparando textos y revisado a mano los dudosos).
  Si cambias el ePub de Valtorta (otros párrafos), habría que rehacer esta tabla.
- En la app: punto naranja junto al Evangelio del día en la portada; en los capítulos de los Evangelios, un círculo
  naranja junto al título muestra/oculta los puntos de cada pasaje; en el libro, cada pasaje lleva encima sus citas.
