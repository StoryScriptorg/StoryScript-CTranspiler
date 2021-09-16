from lexer import Lexer, SymbolTable, libraryIncluded
from tqdm import tqdm
from time import perf_counter
import tracemalloc
import argparse

GlobalVariableTable = SymbolTable()
STORYSCRIPT_INTERPRETER_DEBUG_MODE = True

def parse_string_list(self, command):
	res = ""
	for i in command:
		res += i + " "
	res = res[:-1]
	return res

def parse_file(out_file, file_name, auto_reallocate=True, minified=False):
	"""
	This method read the file and give it to the Parser, Then write the output data to file.
	[PARAMETERS]
	out_file = Output file name
	file_name = Input file name
	auto_reallocate = Turn on auto memory reallocation in the Output code or not.
	minified = Tell the file writer to minify the file or not.
	"""
	tracemalloc.start()
	start_time = perf_counter()
	if STORYSCRIPT_INTERPRETER_DEBUG_MODE: # Check if the run mode was Debug mode or not.
		from os import getcwd
		print("[DEBUG] Current Working Directory: " + getcwd()) # Prints the current working directory
	try:
		f = open(file_name, "r") # Try open the file
	except FileNotFoundError:
		print(f"Cannot open file {fileName}. File does not exist.") # Print the error and terminate the function If the file does not exist.
		return
	if STORYSCRIPT_INTERPRETER_DEBUG_MODE and not auto_reallocate:
		# a Debug message telling that autoreallocate is turned off.
		print("[DEBUG] Auto reallocate turned off.")
	# Creates a new Lexer for the Parsing operation
	lexer = Lexer(GlobalVariableTable, out_file, auto_reallocate=auto_reallocate)
	lexer.file_helper.minified = minified
	# Read all the lines from the file
	lines = f.readlines()
	line_index = 0
	print("Conversion starting...")
	# Looping through all lines. While using tqdm to update the progress bar as well.
	for i in tqdm(lines, ncols=75):
		line_index += 1
		commands = i.split()
		# Insert the returned C code into the File content.
		try:
			if minified and len(commands) != 0 and commands[0] == "//":
				continue
			lexer.file_helper.insert_content(lexer.analyseCommand(commands, ln=line_index)[0])
		except Exception:
			from traceback import print_exc
			print_exc()
			print(commands)
	print("Conversion done. Writing data to file...")
	# Include all libraries
	for i in libraryIncluded:
		lexer.file_helper.insert_header(f"#include <{i}>")
	# Add Exception raising functionality to the C code
	lexer.file_helper.insert_header('''
// Exception Raising
void raiseException(int code, char* description)
{
	switch(code)
	{
		case 100:
			printf("InvalidSyntax: %s", description);
			break;
		case 101:
			printf("AlreadyDefined: %s", description);
			break;
		case 102:
			printf("NotImplementedException %s", description);
			break;
		case 103:
			printf("NotDefinedException: %s", description);
			break;
		case 104:
			printf("GeneralException: %s", description);
			break;
		case 105:
			printf("DivideByZeroException: %s", description);
			break;
		case 106:
			printf("InvalidValue: %s", description);
			break;
		case 107:
			printf("InvalidTypeException: %s", description);
			break;
	}
	exit(code);
}
''')
	lexer.file_helper.insert_header("int main() {")
	lexer.file_helper.write_data_to_file()
	print("Successfully written data to file.")
	# Prints out statistics when done running.
	print(" -- Statistics -- ")
	current, peak = tracemalloc.get_traced_memory()
	finish_time = perf_counter()
	print(f'Memory usage:\t\t {current / 10**6:.6f} MB \n'
		  f'Peak memory usage:\t {peak / 10**6:.6f} MB ')
	print(f'Time elapsed in seconds: {finish_time - start_time:.6f}')
	print("-"*40)
	# Stop the memory allocation tracking
	tracemalloc.stop()

if __name__ == "__main__":
	# python processor.py -o main.c -i main.sts
	print("// StoryScript C Transpiler // Version Alpha 1 //")
	parser = argparse.ArgumentParser(description="Transpile StoryScript code into C code.")
	parser.add_argument(
		"-i", "--input", 
		help="The input file.", 
		required=True
	)
	parser.add_argument(
		"-o", "--output", 
		help="The target output file.", 
		required=True
	)
	parser.add_argument(
		"-no-realloc", 
		"--no-auto-reallocate", 
		action="store_true",
		help="Tell the transpiler to not auto-reallocate memory."
	)
	parser.add_argument( 
		"--minified", 
		action="store_true",
		help="Tell the file writer to minify the output file or not."
	)
	args = parser.parse_args()
	parse_file(args.output, args.input, not args.no_auto_reallocate, args.minified)
