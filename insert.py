import xml.etree.ElementTree as ET
import os
import zipfile
import tempfile
import shutil


def generate_insert_statements(xml_file):
    # Extraer el nombre de la tabla del nombre del archivo
    base_name = os.path.basename(xml_file)
    table_name = base_name.split('.')[1].replace('.xml', '')  # Obtener el texto después del punto y eliminar .xml

    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    inserts = []
    
    for element in root.findall('.//ROW'):  # Cambia 'ROW' al nombre del nodo que contiene los datos
        columns = []
        values = []
        
        for child in element:
            columns.append(child.tag)
            value = child.text
            
            # Aplicar TO_DATE si el nombre del campo contiene "FECHA"
            if "FECHA" in child.tag.upper() and value:
                value = f"TO_DATE('{value}', 'yyyy-mm-dd hh24:mi:ss')"
            else:
                value = f"'{value}'" if value else 'NULL'  # Manejar valores nulos
            
            values.append(value)
        
        columns_str = ', '.join(columns)
        values_str = ', '.join(values)
        insert_statement = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});"
        inserts.append(insert_statement)
    
    return inserts


def process_directory(directory, out):
    all_inserts = []

    # Crear un directorio temporal para descomprimir los archivos zip
    with tempfile.TemporaryDirectory() as temp_dir:
        for filename in os.listdir(directory):
            if filename.endswith('.zip'):
                zip_file_path = os.path.join(directory, filename)

                # Descomprimir el archivo zip en el directorio temporal
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

        # Procesar los archivos XML descomprimidos
        for xml_filename in os.listdir(temp_dir):
            if xml_filename.endswith('.xml'):
                xml_file_path = os.path.join(temp_dir, xml_filename)
                insert_statements = generate_insert_statements(xml_file_path)

                # Guardar cada conjunto de inserts en un archivo separado
                output_file = os.path.join(
                    out, f"{xml_filename.replace('.xml', '')}.sql")

                if len(insert_statements) > 0:
                    with open(output_file, 'w') as f:
                        f.write('SET DEFINE OFF;' + '\n')
                        for statement in insert_statements:
                            f.write(statement + '\n')
                        f.write('COMMIT;' + '\n')
                        f.write('EXIT;' + '\n')


if __name__ == "__main__":
    directory_path = './mulat'  # Cambia esto por la ruta de tu carpeta
    out_path = './sentencias'  # Cambia esto por la ruta de tu carpeta
    process_directory(directory_path, out_path)
