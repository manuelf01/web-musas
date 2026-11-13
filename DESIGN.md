---
name: Las de Siempre — Neo-brasa
description: Sistema visual cálido y claro para pedidos y operación de una hamburguesería nocturna.
colors:
  primary: "#DB4200"
  primary-deep: "#B23400"
  primary-press: "#A12D00"
  secondary: "#F5C842"
  charcoal: "#1A1512"
  charcoal-raised: "#26201C"
  charcoal-muted: "#38302B"
  cream: "#FBF7F0"
  cream-soft: "#FDF1EC"
  surface: "#FFFFFF"
  border: "#E7DFD5"
  text-muted: "#6B6157"
  success: "#2E7D5B"
  danger: "#C4331D"
  dark-background: "#25211e"
  dark-surface: "#2b2622"
  dark-raised: "#332d28"
  dark-soft: "#3a332d"
  dark-border: "#51473f"
  dark-control-border: "#695d53"
  dark-text: "#f0e8df"
  dark-muted: "#c7bbb0"
  dark-accent: "#e9a886"
  dark-brasa: "#a84f2d"
  dark-brasa-deep: "#8e4227"
  dark-brasa-press: "#773821"
typography:
  display:
    fontFamily: "Space Grotesk, system-ui, sans-serif"
    fontSize: "clamp(40px, 12vw, 56px)"
    fontWeight: 700
    lineHeight: 1.05
  headline:
    fontFamily: "Space Grotesk, system-ui, sans-serif"
    fontSize: "34px"
    fontWeight: 700
    lineHeight: 1.2
  title:
    fontFamily: "Space Grotesk, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Space Grotesk, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.4
rounded:
  control: "12px"
  card: "20px"
  pill: "999px"
spacing:
  gutter: "clamp(16px, 4vw, 40px)"
  section: "clamp(52px, 8vw, 96px)"
  control-height: "48px"
  nav-desktop: "80px"
  nav-mobile: "64px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "12px 20px"
    height: "48px"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.charcoal}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "11px 18px"
    height: "44px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.charcoal}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 14px"
    height: "48px"
  chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.charcoal}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "8px 14px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.charcoal}"
    rounded: "{rounded.card}"
    padding: "24px"
---

# Design System: Las de Siempre

## Overview

**Creative North Star: "Neo-brasa nocturna: calidez de brasa y claridad operativa"**

La interfaz toma la calidez de una hamburguesería a la brasa y la convierte en una herramienta cotidiana, fácil de leer tanto para quien pide desde el teléfono como para quien atiende caja, cocina e inventario. La marca se expresa con crema, carbón cálido, brasa tostada y mostaza; las superficies y controles redondeados hacen que las acciones se sientan accesibles sin quitarle precisión al trabajo.

La tienda y el panel comparten tipografía, acentos, bordes y comportamiento de controles. La tienda dispone de más espacio para producto y fotografía; el panel prioriza lectura rápida, tablas y datos operativos. El tema oscuro conserva matices de carbón y café para que el cambio de tema no se sienta como una inversión brusca ni dependa de negro absoluto. Los documentos de comanda y comprobantes destinados a impresión mantienen su presentación clara.

**Key Characteristics:**
- Cálido y artesanal, con lectura operativa directa.
- Una sola identidad para tienda y panel, adaptada a tareas distintas.
- Superficies crema en claro y carbón cálido en oscuro.
- Brasa para acciones y selección; mostaza para énfasis puntuales.
- Controles cómodos, foco visible y diseño adaptable a móvil.

## Colors

La paleta combina **brasa tostada, mostaza cálida, crema y carbón**. Los tonos claros son la base de lectura; el modo oscuro usa superficies escalonadas de carbón con texto marfil y acentos suavizados.

### Primary
- **Brasa tostada** (`#DB4200`): acción principal, selección activa y llamadas a la acción en el tema claro.
- **Brasa profunda** (`#B23400`): estado hover/foco del botón principal.
- **Brasa de presión** (`#A12D00`): estado activo del botón principal.

### Secondary
- **Mostaza cálida** (`#F5C842`): énfasis, pequeños indicadores y estados que necesitan distinguirse sin competir con la acción principal.

### Neutral
- **Carbón** (`#1A1512`): texto principal y superficies de marca oscuras.
- **Carbón elevado** (`#26201C`) y **carbón suave** (`#38302B`): niveles de superficie en elementos oscuros.
- **Crema** (`#FBF7F0`) y **crema rosada** (`#FDF1EC`): fondo de página y superficies cálidas en tema claro.
- **Superficie blanca** (`#FFFFFF`): tarjetas y controles claros.
- **Borde cálido** (`#E7DFD5`): contornos y separadores de bajo contraste.
- **Texto secundario** (`#6B6157`): descripciones y metadatos en superficies claras.
- **Fondo carbón** (`#25211e`), **superficie nocturna** (`#2b2622`), **superficie elevada** (`#332d28`) y **superficie suave** (`#3a332d`): capas del tema oscuro.
- **Borde nocturno** (`#51473f`) y **borde de control nocturno** (`#695d53`): delimitación de tarjetas y campos oscuros.
- **Texto marfil** (`#f0e8df`) y **texto secundario nocturno** (`#c7bbb0`): lectura principal y secundaria en modo oscuro.
- **Acento claro nocturno** (`#e9a886`): enlaces y acentos con contraste más amable sobre carbón.

### Tertiary
- **Brasa nocturna** (`#a84f2d`), **brasa nocturna profunda** (`#8e4227`) y **brasa nocturna de presión** (`#773821`): variantes del acento para tema oscuro, menos luminosas que la brasa del tema claro.

### Semantic
- **Verde éxito** (`#2E7D5B`): confirmaciones y estados correctos.
- **Rojo peligro** (`#C4331D`): errores y operaciones destructivas; reservarlo para comunicar riesgo.

### Named Rules
**The Warm Contrast Rule.** El modo oscuro usa carbón cálido y superficies diferenciadas; no reemplaces la paleta por negro absoluto ni por texto blanco de bajo contraste sobre tarjetas claras.

**The Accent-as-Action Rule.** La brasa señala acciones y selecciones importantes. Mantén la mostaza para énfasis pequeños y evita convertir ambos acentos en decoración dominante.

## Typography

**Display Font:** Space Grotesk (con `system-ui, sans-serif` como alternativa)

**Body Font:** Inter (con `system-ui, sans-serif` como alternativa)

**Label/Mono Font:** Space Grotesk para etiquetas y cifras destacadas; no hay una familia monoespaciada global establecida.

**Character:** Space Grotesk aporta personalidad a títulos, controles y datos clave; Inter sostiene párrafos, formularios y tablas. Las fuentes se sirven desde archivos locales para mantener la identidad sin depender de Google Fonts.

### Hierarchy
- **Display** (700, `clamp(40px, 12vw, 56px)`, 1.05): mensaje principal de la portada y titulares de alto impacto.
- **Headline** (700, 34px; 26px en panel estrecho): títulos de página del panel y secciones principales.
- **Title** (600–700, 18–20px, 1.3): tarjetas, modales y subsecciones.
- **Body** (400–700, 15px, 1.55): instrucciones, descripción y campos; utiliza Inter.
- **Label** (600–700, 12–14px, 1.4): controles, estados y metadatos. El uso de mayúsculas se reserva para etiquetas breves y espaciadas.

### Named Rules
**The Two-Font Rule.** Usa Space Grotesk para jerarquía y énfasis; usa Inter para lectura continua. No añadas una tercera fuente para resolver una variación de estilo.

## Layout

El espacio se adapta al tipo de tarea: tienda y cabeceras usan un ancho máximo de 1440px; el panel puede crecer hasta 1600px para tablas; el detalle de producto limita a 1200px y las vistas de lectura a 900px. El margen lateral es fluido (`clamp(16px, 4vw, 40px)`) y el ritmo entre secciones también escala con la pantalla (`clamp(52px, 8vw, 96px)`).

En escritorio, la navegación principal de la tienda permanece disponible al desplazarse y la barra de categorías queda debajo. El panel combina navegación lateral y barra superior. En móvil, el contenido pasa a columnas simples, los controles se reordenan y la navegación se compacta; las tablas deben conservar acceso a sus datos sin provocar desbordamiento horizontal. La cabecera principal mide 80px en escritorio y 64px en móvil.

**The Task-Width Rule.** Usa el ancho amplio para explorar y operar, pero conserva una columna de lectura acotada para confirmaciones, historial y documentos.

## Elevation & Depth

La profundidad es cálida y discreta. Los bordes suaves separan grupos en reposo; las sombras ambientales distinguen tarjetas del fondo y aumentan solo en interacción, sin convertir cada elemento en una superficie flotante. Las capas del modo oscuro se diferencian por tono y borde, no por brillos duros.

### Shadow Vocabulary
- **Elevación de tarjeta** (`0 8px 24px rgba(26, 21, 18, 0.08)`): tarjetas y módulos sobre la base clara.
- **Elevación al interactuar** (`0 12px 32px rgba(26, 21, 18, 0.12)`): hover en tarjetas interactivas.
- **Elevación nocturna** (`0 8px 24px rgba(16, 12, 9, .22)`): capas en modo oscuro.
- **Elevación nocturna interactiva** (`0 12px 32px rgba(16, 12, 9, .3)`): respuesta hover en tema oscuro.

### Named Rules
**The Warm Layer Rule.** Separa contenido con tono y borde primero; eleva con sombra suave cuando una tarjeta necesita distinguirse o responde al puntero.

## Shapes

La geometría es amable, consistente y táctil: tarjetas con esquinas de 20px, campos y botones con esquinas de 12px, y chips o insignias completamente redondeados. Los bordes son finos y cálidos. Mantén el radio grande para grupos de contenido y evita mezclar esquinas agudas con controles redondeados dentro del mismo patrón.

## Components

### Buttons
- **Primary:** botón de brasa tostada con texto blanco, tipografía Space Grotesk semibold, esquina de 12px, altura mínima de 48px y sombra cálida. En hover se oscurece; al presionarlo baja un píxel. El foco debe permanecer visible.
- **Outline:** superficie transparente, borde cálido, texto carbón, esquina de 12px y altura mínima de 44px. El hover puede mostrar una superficie blanca y sombra discreta.
- **Danger:** reserva el tono de peligro para confirmar acciones destructivas; incluye texto explícito además del color.

### Inputs
- Campos de 48px de alto, borde cálido de 1px, fondo blanco en claro, texto Inter de 15px y esquina de 12px.
- El foco cambia el borde a brasa y presenta un anillo visible de 3px. En modo oscuro, el campo debe adoptar superficie y texto nocturnos legibles.
- Los mensajes de ayuda y validación deben acompañar al campo y no depender solo del color.

### Navigation
- La tienda mantiene marca, enlaces clave, carrito y cuenta en su cabecera de escritorio; la navegación de categorías se organiza en una segunda franja.
- El panel usa barra superior y navegación lateral, con el contenido de trabajo en una columna flexible.
- En móvil, prioriza las rutas de uso frecuente y evita que marca, carrito y enlaces compitan por el mismo ancho.
- El elemento activo combina color y señal visual adicional, como borde, fondo o indicador.

### Chips
- Forma de píldora, borde cálido, espaciado compacto y Space Grotesk semibold.
- La categoría seleccionada usa fondo brasa y texto claro; el estado no seleccionado permanece neutro.
- Estados y contadores usan colores semánticos sin sacrificar contraste.

### Cards
- Tarjetas blancas o crema sobre fondo claro; en oscuro, superficies carbón escalonadas.
- Esquina de 20px, borde fino, padding típico de 22–24px y sombra ambiental suave.
- Los paneles de KPI, contenido y detalle comparten la misma base visual; la jerarquía la dan el título, el espacio y la organización de datos.

### Modals
- Usa modales para operaciones breves y confirmaciones con consecuencias. Mantén título, explicación, campos y acciones claramente separados.
- El fondo atenuado y la tarjeta de esquinas redondeadas deben conservar legibles las acciones primaria y secundaria en ambos temas.
- Confirmaciones destructivas explican el efecto y ofrecen una salida segura; no dependas de `window.confirm()`.

### Theme
- Un interruptor claro/oscuro conserva la preferencia en el dispositivo; la primera visita puede seguir la preferencia del sistema.
- Aplicar `data-theme="dark"` con las mismas variables semánticas, ajustando fondos, texto, bordes, formularios, tablas y modales.
- Antes de publicar una vista, revisa ambas apariencias: texto en superficies, controles, estados, navegación, loader y alertas.
- Comandas y comprobantes destinados a impresión permanecen claros.

### Named Rules
**The Touch-and-Read Rule.** Los controles deben ofrecer áreas cómodas y estados perceptibles; el acento guía la acción mientras el texto comunica su propósito.

## Do's and Don'ts

### Do
- Mantén la marca Las de Siempre y su símbolo de hamburguesa vectorial.
- Usa la pareja local Inter + Space Grotesk y los tokens existentes antes de crear variantes.
- Comprueba texto, controles, navegación, modales y estados en tema claro y oscuro.
- Conserva bordes visibles, foco perceptible y alternativas textuales a los indicadores por color.
- Diseña la tienda para uso móvil y el panel para lectura y operación rápida.
- Usa la elevación como respuesta o separación sutil, no como decoración constante.

### Don't
- No uses negro absoluto como base del tema oscuro ni inviertas colores de forma automática sin revisar cada superficie.
- No coloques texto blanco pálido sobre tarjetas blancas o crema, ni texto carbón sobre superficies carbón.
- No inventes nuevas familias tipográficas, radios o sombras si los tokens actuales resuelven el patrón.
- No uses la brasa para colorear todo el contenido; resérvala para acciones y selección.
- No hagas que un estado dependa únicamente del color ni ocultes el foco del teclado.
