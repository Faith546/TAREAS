    /*
    * Building Generator - Generador de edificios cilíndricos en formato OBJ
    * 
    * Crea edificios con forma de cilindro truncado con parámetros personalizables:
    * - Número de lados (3-36)
    * - Altura del edificio (flotante positivo)
    * - Radio en la base (flotante positivo)
    * - Radio en la cima (flotante positivo)
    * 
    * CG_2 - TC2008B
    * 2025-11-23
    */

    import { V3 } from './3d-lib';

    function generateBuilding(sides = 8, height = 6.0, baseRadius = 1.0, topRadius = 0.8) {
    if (sides < 3 || sides > 36) {
        sides = 8;
    }

    if (height <= 0) height = 6.0;
    if (baseRadius <= 0) baseRadius = 1.0;
    if (topRadius <= 0) topRadius = 0.8;

    const vertices = [];
    const faces = [];
    const faceNormals = [];

    // Centro de la base primero
    vertices.push({ x: 0, y: 0, z: 0 });
    // Centro de la cima segundo
    vertices.push({ x: 0, y: height, z: 0 });

    // Generar vértices intercalados: base[i], cima[i], base[i+1], cima[i+1], ...
    for (let i = 0; i < sides; i++) {
        const angle = (2 * Math.PI * i) / sides;
        
        // Vértice en la base
        const xBase = baseRadius * Math.cos(angle);
        const zBase = baseRadius * Math.sin(angle);
        vertices.push({ x: xBase, y: 0, z: zBase });
        
        // Vértice en la cima
        const xTop = topRadius * Math.cos(angle);
        const zTop = topRadius * Math.sin(angle);
        vertices.push({ x: xTop, y: height, z: zTop });
    }

    // Generar caras laterales
    for (let i = 0; i < sides; i++) {
        const baseIdx1 = 3 + i * 2;           // vértice base actual
        const topIdx1 = 4 + i * 2;            // vértice cima actual
        const baseIdx2 = 3 + ((i + 1) % sides) * 2;  // vértice base siguiente
        const topIdx2 = 4 + ((i + 1) % sides) * 2;   // vértice cima siguiente

        // Triángulo inferior de la cara lateral
        faces.push([baseIdx1, baseIdx2, 1]);
        faceNormals.push(calculateFaceNormal(vertices, baseIdx1 - 1, baseIdx2 - 1, 0));

        // Triángulo superior de la cara lateral
        faces.push([topIdx1, 2, topIdx2]);
        faceNormals.push(calculateFaceNormal(vertices, topIdx1 - 1, 1, topIdx2 - 1));

        // Dos triángulos del lado
        faces.push([baseIdx1, topIdx1, baseIdx2]);
        faceNormals.push(calculateFaceNormal(vertices, baseIdx1 - 1, topIdx1 - 1, baseIdx2 - 1));

        faces.push([topIdx1, baseIdx2, topIdx2]);
        faceNormals.push(calculateFaceNormal(vertices, topIdx1 - 1, baseIdx2 - 1, topIdx2 - 1));
    }

    // Generar string OBJ
    let objContent = `# OBJ file building_${sides}_${height}_${baseRadius}_${topRadius}.obj\n`;
    objContent += `# ${vertices.length} vertices\n`;

    // Escribir vértices
    for (const v of vertices) {
        objContent += `v ${v.x.toFixed(4)} ${v.y.toFixed(4)} ${v.z.toFixed(4)}\n`;
    }

    // Escribir normales
    objContent += `# ${faceNormals.length} normals\n`;
    for (const n of faceNormals) {
        objContent += `vn ${n.x.toFixed(4)} ${n.y.toFixed(4)} ${n.z.toFixed(4)}\n`;
    }

    // Escribir caras
    objContent += `# ${faces.length} faces\n`;
    for (let i = 0; i < faces.length; i++) {
        const face = faces[i];
        const normalIdx = i + 1;
        objContent += `f ${face[0]}//${normalIdx} ${face[1]}//${normalIdx} ${face[2]}//${normalIdx}\n`;
    }

    return objContent;
    }


    function calculateFaceNormal(vertices, idx0, idx1, idx2) {
    const v0 = vertices[idx0];
    const v1 = vertices[idx1];
    const v2 = vertices[idx2];

    // Crear vectores V3
    const vec0 = V3.create(v0.x, v0.y, v0.z);
    const vec1 = V3.create(v1.x, v1.y, v1.z);
    const vec2 = V3.create(v2.x, v2.y, v2.z);

    // Calcular aristas
    const edge1 = V3.subtract(vec1, vec0);
    const edge2 = V3.subtract(vec2, vec0);

    // Calcular normal de la cara usando producto cruz
    const faceNormal = V3.cross(edge1, edge2);

    // Normalizar la normal
    const normalized = V3.normalize(faceNormal);

    return {
        x: normalized[0],
        y: normalized[1],
        z: normalized[2]
    };
    }


    function main() {
    // Obtener parámetros de la línea de comandos o usar valores por defecto
    const args = process.argv.slice(2);
    
    const sides = args[0] ? parseInt(args[0]) : 8;
    const height = args[1] ? parseFloat(args[1]) : 6.0;
    const baseRadius = args[2] ? parseFloat(args[2]) : 1.0;
    const topRadius = args[3] ? parseFloat(args[3]) : 0.8;

    // Validar que los valores sean correctos
    if (sides < 3 || sides > 36) {
        console.error('Error: El número de lados debe estar entre 3 y 36');
        process.exit(1);
    }

    if (height <= 0 || baseRadius <= 0 || topRadius <= 0) {
        console.error('Error: La altura y los radios deben ser positivos');
        process.exit(1);
    }

    // Generar el edificio
    const objContent = generateBuilding(sides, height, baseRadius, topRadius);
    
    // Imprimir a stdout para redireccionar a archivo
    console.log(objContent);
    }

    // Si se ejecuta como script
    if (typeof process !== 'undefined' && process.argv) {
    main();
    }

    export { generateBuilding };
