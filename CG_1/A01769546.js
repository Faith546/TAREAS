/*
 * Script para dibujar figuras complejas. Implementación de transformaciones
 * (escala, traslación, rotación). Se rota una figura compuesta por diferentes
 *  objetos, rotando alrededor de un pivote.s
 *
 * Diego Flores Becerril
 * 2025-11-14
 */


'use strict';

import * as twgl from 'twgl-base.js';
import { M3 } from './2d-lib.js';
import GUI from 'lil-gui';

// Define the shader code, using GLSL 3.00

const vsGLSL = `#version 300 es
in vec2 a_position;

uniform vec2 u_resolution;
uniform mat3 u_transforms;

void main() {
    // Multiply the matrix by the vector, adding 1 to the vector to make
    // it the correct size. Then keep only the two first components
    vec2 position = (u_transforms * vec3(a_position, 1)).xy;

    // Convert the position from pixels to 0.0 - 1.0
    vec2 zeroToOne = position / u_resolution;

    // Convert from 0->1 to 0->2
    vec2 zeroToTwo = zeroToOne * 2.0;

    // Convert from 0->2 to -1->1 (clip space)
    vec2 clipSpace = zeroToTwo - 1.0;

    // Invert Y axis
    //gl_Position = vec4(clipSpace[0], clipSpace[1] * -1.0, 0, 1);
    gl_Position = vec4(clipSpace * vec2(1, -1), 0, 1);
}
`;

const fsGLSL = `#version 300 es
precision highp float;

uniform vec4 u_color;

out vec4 outColor;

void main() {
    outColor = u_color;
}
`;


// Estructura para la data global de todos los objetos
// La data sera modificada por la UI y utilizada por el renderizador
const objects = {
    circle: {
        transforms: {
            t: {
                x: 600,
                y: 330,
                z: 0,
            },
            rr: {
                x: 0,
                y: 0,
                z: 0,
            },
            s: {
                x: 1,
                y: 1,
                z: 1,
            }
        },
        color: [1, 0.843, 0, 1],
    },
    pivot: {
        transforms: {
            t: {
                x: 600,  
                y: 330,
                z: 0,
            },
            rr: {
                x: 0,
                y: 0,
                z: 0,
            },
            s: {
                x: 1,  
                y: 1,
                z: 1,
            }
        },
        color: [0.5, 0.3, 0.7, 1],
    },
    leftEye: {
        transforms: {
            t: {
                x: -60,  
                y: -50,
                z: 0,
            },
            rr: { 
                x: 0,
                y: 0, 
                z: 0 
            },
            s: {
                x: 1, 
                y: 1, 
                z: 1 
            }
        },
        color: [0, 0, 0, 1],  
    },
    rightEye: {
        transforms: {
            t: {
                x: 60,  
                y: -50,
                z: 0,
            },
            rr: { 
                x: 0,
                y: 0, 
                z: 0 
            },
            s: { 
                x: 1, 
                y: 1, 
                z: 1 
            }
        },
        color: [0, 0, 0, 1],
    },
    mouth: {
        transforms: {
            t: {
                x: 0,
                y: 60,
                z: 0,
            },
            rr: { 
                x: 0, 
                y: 0, 
                z: 100 
            },
            s: {
                x: 1,
                y: 1,
                z: 1
                }
        },
        color: [0, 0, 0, 1],
    },
}


// Inicializacion del entorno de WebGL
function main() {
    const canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl2');
    twgl.resizeCanvasToDisplaySize(gl.canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    setupUI(gl);

    const programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);

    // Circulo
    // Variables para generar el poligono utilizando la funcion generateData(num lados, centro X, centro Y, radio)
    const sidesCircle = 12;
    const centerXCircle = 0;
    const centerYCircle = 0;
    const radiusCircle = 200;

    // Creacion de un poligono con centro en una ubicacion en especifico
    const arraysCircle = generateData(sidesCircle, centerXCircle, centerYCircle, radiusCircle);
    const bufferinfoCircle = twgl.createBufferInfoFromArrays(gl, arraysCircle);
    const vaoCircle = twgl.createVAOFromBufferInfo(gl, programInfo, bufferinfoCircle);

     // Pivote
    const sidesPivot = 4;
    const centerXPivot = 0;
    const centerYPivot = 0;
    const radiusPivot = 10;

    const arrays2 = generateData(sidesPivot, centerXPivot, centerYPivot, radiusPivot);
    const bufferInfo2 = twgl.createBufferInfoFromArrays(gl, arrays2);
    const vao2 = twgl.createVAOFromBufferInfo(gl, programInfo, bufferInfo2);

     // Ojo izquierdo (círculo pequeño)
    const sidesEye = 20;
    const centerXEye = 0;
    const centerYEye = 0;
    const radiusEye = 20;

    const arraysLeftEye = generateData(sidesEye, centerXEye, centerYEye, radiusEye);
    const bufferInfoLeftEye = twgl.createBufferInfoFromArrays(gl, arraysLeftEye);
    const vaoLeftEye = twgl.createVAOFromBufferInfo(gl, programInfo, bufferInfoLeftEye);

    // Ojo derecho (círculo pequeño)
    const arraysRightEye = generateData(sidesEye, centerXEye, centerYEye, radiusEye);
    const bufferInfoRightEye = twgl.createBufferInfoFromArrays(gl, arraysRightEye);
    const vaoRightEye = twgl.createVAOFromBufferInfo(gl, programInfo, bufferInfoRightEye);

    // Boca (triángulo)
    const sidesMouth = 3;
    const centerXMouth = 0;
    const centerYMouth = 0;
    const radiusMouth = 80;

    const arraysMouth = generateData(sidesMouth, centerXMouth, centerYMouth, radiusMouth);
    const bufferInfoMouth = twgl.createBufferInfoFromArrays(gl, arraysMouth);
    const vaoMouth = twgl.createVAOFromBufferInfo(gl, programInfo, bufferInfoMouth);

    // Renderizar los objetos en la escena con drawScene(gl)
    drawScene(gl, [
        {vao: vaoCircle, bufferInfo: bufferinfoCircle, objectKey: 'circle'},
        {vao: vao2, bufferInfo: bufferInfo2, objectKey: 'pivot'},
        {vao: vaoLeftEye, bufferInfo: bufferInfoLeftEye, objectKey: 'leftEye'},
        {vao: vaoRightEye, bufferInfo: bufferInfoRightEye, objectKey: 'rightEye'},
        {vao: vaoMouth, bufferInfo: bufferInfoMouth, objectKey: 'mouth'},
    ], programInfo);
}

// Función para renderizar todos los objetos en la escena
function drawScene(gl, renderObjects, programInfo) {

    gl.useProgram(programInfo.program);

    for (let renderObj of renderObjects) {
        const obj = objects[renderObj.objectKey];

        // Inicializar con la matriz identidad
        let transforms = M3.identity();
        
        // Transformaciones jerárquicas: circle y sus elementos (ojos, boca) rotan alrededor del pivote
        if (['circle', 'leftEye', 'rightEye', 'mouth'].includes(renderObj.objectKey)){
            let translate = [obj.transforms.t.x, obj.transforms.t.y];
            let angle_radians = obj.transforms.rr.z;
            let scale = [obj.transforms.s.x, obj.transforms.s.y];
            
            // Obtener la posición del pivote (pivot)
            let pivotPos = [objects.pivot.transforms.t.x, objects.pivot.transforms.t.y];

            // JERARQUÍA: Si es un elemento hijo (ojo o boca), heredar transformaciones de circle
            if (renderObj.objectKey !== 'circle') {
                let circlePos = [objects.circle.transforms.t.x, objects.circle.transforms.t.y];
                let circleRotation = objects.circle.transforms.rr.z;
                let circleScale = [objects.circle.transforms.s.x, objects.circle.transforms.s.y];
                
                // 1. Crear matrices de transformaciones locales del elemento hijo
                const scaMat = M3.scale(scale);
                const rotMat = M3.rotation(angle_radians);
                const traMat = M3.translation(translate);
                
                // 2. Aplicar transformaciones locales: S -> R -> T (posición relativa al padre)
                transforms = M3.multiply(scaMat, transforms);
                transforms = M3.multiply(rotMat, transforms);
                transforms = M3.multiply(traMat, transforms);
                
                // 3. Heredar transformaciones del padre (circle)
                const scaMat1 = M3.scale(circleScale);
                const rotMat1 = M3.rotation(circleRotation);
                
                // 4. Calcular offset desde el pivote hasta circle
                const translateObjMat = M3.translation([circlePos[0] - pivotPos[0], circlePos[1] - pivotPos[1]]);
                const translateBackMat = M3.translation(pivotPos);
                
                // 5. Aplicar transformaciones del padre: S_padre -> T_offset -> R_padre -> T_pivote
                // ORDEN CRUCIAL: esto hace que el hijo rote junto con el padre alrededor del pivote
                transforms = M3.multiply(scaMat1, transforms);
                transforms = M3.multiply(translateObjMat, transforms);
                transforms = M3.multiply(rotMat1, transforms);
                transforms = M3.multiply(translateBackMat, transforms);
                
            } else {
                // Para circle (la cara principal) - rotar alrededor del pivote
                const scaMat = M3.scale(scale);
                const rotMat = M3.rotation(angle_radians);
                const translateBackMat = M3.translation(pivotPos);
                const translateObjMat = M3.translation([translate[0] - pivotPos[0], translate[1] - pivotPos[1]]);

                // ROTACIÓN ALREDEDOR DEL PIVOTE: S -> T_offset -> R -> T_pivote
                // 1. Escalar
                // 2. Posicionar relativo al pivote
                // 3. Rotar alrededor del origen (que es el pivote)
                // 4. Trasladar de vuelta a la posición del pivote
                transforms = M3.multiply(scaMat, transforms);
                transforms = M3.multiply(translateObjMat, transforms);
                transforms = M3.multiply(rotMat, transforms);
                transforms = M3.multiply(translateBackMat, transforms);
            }
        }else{
            // Objetos independientes (pivot) - transformaciones normales
            let translate = [obj.transforms.t.x, obj.transforms.t.y];
            let angle_radians = obj.transforms.rr.z;
            let scale = [obj.transforms.s.x, obj.transforms.s.y];

            // Crear matrices de transformación
            const scaMat = M3.scale(scale);
            const rotMat = M3.rotation(angle_radians);
            const traMat = M3.translation(translate);

            // Orden estándar de transformaciones: S -> R -> T
            transforms = M3.multiply(scaMat, transforms);
            transforms = M3.multiply(rotMat, transforms);
            transforms = M3.multiply(traMat, transforms);
        }


        // Uniforms: variables que se pasan al shader
        let uniforms =
        {
            u_resolution: [gl.canvas.width, gl.canvas.height],
            u_transforms: transforms,  // Matriz de transformación compuesta
            u_color: obj.color,
        }

        twgl.setUniforms(programInfo, uniforms);
        gl.bindVertexArray(renderObj.vao);
        twgl.drawBufferInfo(gl, renderObj.bufferInfo);
    }

    // Loop de animación - redibuja la escena en cada frame
    requestAnimationFrame(() => drawScene(gl, renderObjects, programInfo));
}

// Configurar la interfaz de usuario con lil-gui
function setupUI(gl)
{
    const gui = new GUI();

    // Controles para la cara feliz (objeto principal)
    const circleFolder = gui.addFolder('Cara Feliz');
    
    const tra1Folder = circleFolder.addFolder('Translation');
    tra1Folder.add(objects.circle.transforms.t, 'x', 0, gl.canvas.width);
    tra1Folder.add(objects.circle.transforms.t, 'y', 0, gl.canvas.height);

    const rot1Folder = circleFolder.addFolder('Rotation');
    rot1Folder.add(objects.circle.transforms.rr, 'z', 0, Math.PI * 2);

    const sca1Folder = circleFolder.addFolder('Scale');
    sca1Folder.add(objects.circle.transforms.s, 'x', -10, 10);
    sca1Folder.add(objects.circle.transforms.s, 'y', -10, 10);

    circleFolder.addColor(objects.circle, 'color');

    // Controles para el Pivote
    const pivotFolder = gui.addFolder('Pivote');
    
    const tra2Folder = pivotFolder.addFolder('Translation');
    tra2Folder.add(objects.pivot.transforms.t, 'x', 0, gl.canvas.width);
    tra2Folder.add(objects.pivot.transforms.t, 'y', 0, gl.canvas.height);

    pivotFolder.addColor(objects.pivot, 'color');
}

// Función para generar datos de vértices de un polígono regular
// sides: número de lados, centerX/Y: posición del centro, radius: radio del círculo circunscrito
function generateData(sides, centerX, centerY, radius) {
    // Estructura de datos para los vértices
    let arrays =
    {
        a_position: { numComponents: 2, data: [] },  // Posiciones 2D (x, y)
        a_color:    { numComponents: 4, data: [] },  // Colores RGBA
        indices:  { numComponents: 3, data: [] }     // Índices de triángulos (3 vértices)
    };

    // Vértice central del polígono (color blanco)
    arrays.a_position.data.push(centerX);
    arrays.a_position.data.push(centerY);
    arrays.a_color.data.push(1);
    arrays.a_color.data.push(1);
    arrays.a_color.data.push(1);
    arrays.a_color.data.push(1);

    let angleStep = 2 * Math.PI / sides;  // Ángulo entre cada vértice
    
    // Generar vértices del perímetro del polígono
    for (let s=0; s<sides; s++) {
        let angle = angleStep * s;
        
        // Calcular coordenadas usando trigonometría (círculo unitario)
        let x = centerX + Math.cos(angle) * radius;
        let y = centerY + Math.sin(angle) * radius;
        arrays.a_position.data.push(x);
        arrays.a_position.data.push(y);
        
        // Color aleatorio para cada vértice
        arrays.a_color.data.push(Math.random());
        arrays.a_color.data.push(Math.random());
        arrays.a_color.data.push(Math.random());
        arrays.a_color.data.push(1);
        
        // Definir triángulos en sentido antihorario (centro -> vértice actual -> siguiente vértice)
        arrays.indices.data.push(0);
        arrays.indices.data.push(s + 1);
        arrays.indices.data.push(((s + 2) <= sides) ? (s + 2) : 1);
    }
    return arrays;
}

main()
