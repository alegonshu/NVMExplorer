import nvmexplorer_src.input_defs
import os
import numpy as np
#import gspread
import fileinput
#from oauth2client.service_account import ServiceAccountCredentials
import csv

def parse_nvsim_input_file(file_path): # helper function to parse cell cfgs and mem cfgs
  headers = []
  vals = []
  with open(file_path) as fp:
    line = fp.readline()
    while ':' in line:
        header=line.split(':')[0]
        header=header.replace('-','')
        val=line.split(':')[1]
        headers.append(header.rstrip())
        vals.append(val.rstrip())
        line = fp.readline()
  return headers, vals

class ExperimentResult:
  def __init__(self,
		access_pattern = nvmexplorer_src.input_defs.access_pattern.PatternConfig(),
		nvsim_input_cfg = nvmexplorer_src.input_defs.nvsim_interface.NVSimInputConfig(),
		nvsim_output = nvmexplorer_src.input_defs.nvsim_interface.NVSimOutputConfig()
		):
    self.access_pattern = access_pattern
    self.input_cfg = nvsim_input_cfg
    self.output = nvsim_output
    self.total_dynamic_read_power = 0
    self.total_dynamic_write_power = 0
    self.total_power = 0
    self.total_write_energy = 0
    self.total_read_energy = 0
    self.total_energy = 0
    self.total_read_latency = 0
    self.total_write_latency = 0
    self.total_latency = 0
    self.read_bw_utilization = 0
    self.write_bw_utilization = 0
    self.time_until_degraded = 0
    self.read_accesses = 0
    self.write_accesses = 0

  def evaluate(self):
    # compute memory accesses
    self.read_accesses = np.ceil((8 * self.access_pattern.total_reads * self.access_pattern.read_size) / self.input_cfg.word_width) 
    self.write_accesses = np.ceil((8 * self.access_pattern.total_writes * self.access_pattern.write_size) / self.input_cfg.word_width)
    
    # compute latency (ms)
    self.total_read_latency = self.read_accesses * self.output.read_latency / 1000 / 1000
    self.total_write_latency = self.write_accesses * self.output.write_latency / 1000 / 1000
    self.total_latency = self.total_read_latency + self.total_write_latency

    # compute energy (mJ)
    self.total_read_energy = self.read_accesses * self.output.read_energy / 1000 / 1000 / 1000
    self.total_write_energy = self.write_accesses * self.output.write_energy / 1000 / 1000 / 1000
    self.total_energy = self.total_read_energy + self.total_write_energy # TODO: add to csv

    # compute power (mW)
    self.total_dynamic_read_power = (self.total_read_energy / self.total_read_latency) * 1000
    self.total_dynamic_write_power = (self.total_write_energy / self.total_write_latency) * 1000
    self.total_power = (self.total_energy / self.total_latency) * 1000
    # if self.input_cfg.cell_type.mem_cell_type == 'SRAM':
    #    self.total_power += self.output.leakage_power
  
  def report_header(self): #FIXME report all results
    print("Total Dynamic Read Power (mW)\tTotal Dynamic Write Power (mW)\tTotal Power (mW)", end ="\t")
    print("Total Dynamic Read Energy (mJ)\tTotal Dynamic Write Energy (mJ)\tTotal Dynamic Energy (mJ)", end ="\t")
    print("Total Read Latency (ms)\tTotal Write Latency (ms)\tTotal Latency (ms)\tRead BW Util\tWrite BW Util")

  def report_result(self):
    print(self.total_dynamic_read_power, end ="\t")  
    print(self.total_dynamic_write_power, end ="\t")  
    print(self.total_power, end ="\t")
    print(self.total_read_energy, end ="\t")  
    print(self.total_write_energy, end ="\t")  
    print(self.total_energy, end ="\t")  
    print(self.total_read_latency, end="\t")
    print(self.total_write_latency, end ="\t")
    print(self.total_latency, end ="\t")
    print(self.read_bw_utilization, end="\t")
    print(self.write_bw_utilization, end = "\t")
    print()

  def report_header_benchmark(self, to_csv, csv_file_path, cell_cfg_path, mem_cfg_path): #FIXME report all results
    #FIXME: make extra parameters as kwargs
    
    # Remove empty lines from cfg file to make processing easier
    for line in fileinput.FileInput(mem_cfg_path,inplace=1):
        if line.rstrip():
            print(line, end="")

    cell_headers, cell_vals = parse_nvsim_input_file(cell_cfg_path)
    mem_headers, mem_vals = parse_nvsim_input_file(mem_cfg_path)

    row_to_insert = ["Benchmark Name", "Read Accesses", "Write Accesses", "Total Dynamic Read Power (mW)", "Total Dynamic Write Power (mW)", "Total Power (mW)", "Total Dynamic Read Energy (mJ)", "Total Dynamic Write Energy (mJ)", "Total Dynamic Energy (mJ)", "Total Read Latency (ms)", "Total Write Latency (ms)", "Total Latency (ms)", "Total Latency (ms)", "Total Latency (ms)", "Read BW Util", "Write BW Util", "Area (mm^2)", "Area Efficiency (percent)", "Read Latency (ns)", "Write Latency (ns)", "Read Energy (pJ)", "Write Energy (pJ)", "Leakage Power (mW)", "Bits Per Cell"]
    

    cell_headers.extend(mem_headers)
    cell_headers.extend(row_to_insert)
    row_to_insert = cell_headers

    with open(csv_file_path, "a+", newline='') as fp:
      wr = csv.writer(fp, dialect='excel')
      wr.writerow(row_to_insert)

  def report_result_benchmark(self, to_csv, csv_file_path, cell_cfg_path, mem_cfg_path, access_pattern):
    #FIXME: make extra parameters as kwargs
    
    # Remove empty lines from cfg file to make processing easier
    for line in fileinput.FileInput(mem_cfg_path,inplace=1):
        if line.rstrip():
            print(line, end="")

    cell_headers, cell_vals = parse_nvsim_input_file(cell_cfg_path)
    mem_headers, mem_vals = parse_nvsim_input_file(mem_cfg_path)

    if "1BPC" in csv_file_path:
      bits_per_cell = 1
    elif "2BPC" in csv_file_path:
      bits_per_cell = 2
    elif "3BPC" in csv_file_path:
      bits_per_cell = 3
    else:
      bits_per_cell = 1

    row_to_insert = [access_pattern.benchmark_name, self.read_accesses, self.write_accesses, self.total_dynamic_read_power, self.total_dynamic_write_power, self.total_power, self.total_read_energy, self.total_write_energy, self.total_energy, self.total_read_latency, self.total_write_latency, self.total_latency, self.read_bw_utilization, self.write_bw_utilization, self.output.area, self.output.area_efficiency, self.output.read_latency, self.output.write_latency, self.output.read_energy, self.output.write_energy, self.output.leakage_power, bits_per_cell]

    cell_vals.extend(mem_vals)
    cell_vals.extend(row_to_insert)
    row_to_insert = cell_vals
    
    with open(csv_file_path, "a", newline='') as fp:
      wr = csv.writer(fp, dialect='excel')
      wr.writerow(row_to_insert)
 
  def report_header_gSheet(self, to_csv, csv_file_path, cell_cfg_path, mem_cfg_path, write_accesses_header, read_accesses_header, sheet_id): #FIXME report all results
    #FIXME: make extra parameters as kwargs
    
    # Remove empty lines from cfg file to make processing easier
    for line in fileinput.FileInput(mem_cfg_path,inplace=1):
        if line.rstrip():
            print(line, end="")

    cell_headers, cell_vals = parse_nvsim_input_file(cell_cfg_path)
    mem_headers, mem_vals = parse_nvsim_input_file(mem_cfg_path)

    row_to_insert = [write_accesses_header, read_accesses_header, "Total Dynamic Read Power (mW)", "Total Dynamic Write Power (mW)", "Total Power (mW)", "Total Dynamic Read Energy (mJ)", "Total Dynamic Write Energy (mJ)", "Total Dynamic Energy (mJ)", "Total Read Latency (ms)", "Total Write Latency (ms)", "Total Latency (ms)", "Read BW Util", "Write BW Util", "Area (mm^2)", "Area Efficiency (percent)", "Read Latency (ns)", "Write Latency (ns)", "Read Energy (pJ)", "Write Energy (pJ)", "Leakage Power (mW)"]
   
    cell_headers.extend(mem_headers)
    cell_headers.extend(row_to_insert)
    row_to_insert = cell_headers

    if to_csv == 0: # write to gSheet
      # Setup access to Google sheets
      scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
      credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials_ahankin.json", scope)
      client = gspread.authorize(credentials)
      result_sheet = client.open("Results - Systems Perspective Survey of NVM Technologies").worksheet(sheet_id)

      if not result_sheet.row_values(1): # Need to write the header
        #result_sheet.clear()
        result_sheet.append_row(row_to_insert)
    elif to_csv == 1:
      with open(csv_file_path, "a+") as fp:
          wr = csv.writer(fp, dialect='excel')
          wr.writerow(row_to_insert)


  def report_result_gSheet(self, to_csv, csv_file_path, cell_cfg_path, mem_cfg_path, num_write_accesses, num_read_accesses, sheet_id):
    #FIXME: make extra parameters as kwargs
    
    # Remove empty lines from cfg file to make processing easier
    for line in fileinput.FileInput(mem_cfg_path,inplace=1):
        if line.rstrip():
            print(line, end="")

    cell_headers, cell_vals = parse_nvsim_input_file(cell_cfg_path)
    mem_headers, mem_vals = parse_nvsim_input_file(mem_cfg_path)

    row_to_insert = [num_write_accesses, num_read_accesses, self.total_dynamic_read_power, self.total_dynamic_write_power, self.total_power, self.total_read_energy, self.total_write_energy, self.total_energy, self.total_read_latency, self.total_write_latency, self.total_latency, self.read_bw_utilization, self.write_bw_utilization, self.output.area, self.output.area_efficiency, self.output.read_latency, self.output.write_latency, self.output.read_energy, self.output.write_energy, self.output.leakage_power]

    cell_vals.extend(mem_vals)
    cell_vals.extend(row_to_insert)
    row_to_insert = cell_vals
    
    if to_csv == 0:
      # Setup access to Google sheets
      scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
      credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials_ahankin.json", scope)
      client = gspread.authorize(credentials)
      result_sheet = client.open("Results - Systems Perspective Survey of NVM Technologies").worksheet(sheet_id)
      result_sheet.append_row(row_to_insert)
    elif to_csv == 1:
      with open(csv_file_path, "a") as fp:
        wr = csv.writer(fp, dialect='excel')
        wr.writerow(row_to_insert)
