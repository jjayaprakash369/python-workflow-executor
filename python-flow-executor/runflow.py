'''
Created on 04-Nov-2018

@author: JayaprakashJayabalan
'''
import sys
import json
import logging
import subprocess
import shlex
import time


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

input_flow_file='flow-ipis.json'

runtime_environment='dev'

#Parsing the input flow json file and loading it into global flow_dict dictionary 
logging.info('Loading the flow from input flow json')
try:
    with open(input_flow_file, 'r') as f:
        flow_dict = json.load(f)
except Exception as e:
    logging.exception("Exception occurred in loading the input flow file")
    sys.exit(101)

logging.info('Flow loaded successfully')


def executeFlow(flowName):
    logging.info("Starting the flow execution ")
    logging.debug("DEBUG:: Finding the first-step")
    __intial_step__= flow_dict['StartsWith']
    __not_final_step__=True
    __current_step_name__=__intial_step__
    __current_step__=flow_dict[__current_step_name__]
    while(__not_final_step__):
        logging.info("Initiating the step %s",__current_step_name__)
        __response_status__=executeStep(__current_step_name__,__current_step__)
        if __response_status__ != 0:
            logging.error("Error occurred in the step execution. Terminating the flow execution")
            sys.exit(__response_status__)
        __next_step_name__=__current_step__['NEXTSTATE']
        if __next_step_name__ == 'ENDSWITHTHIS' :
            __not_final_step__=False
        else:
            __current_step__=flow_dict[__next_step_name__]
            __current_step_name__=__next_step_name__

def runShell(_command_):
    #_response_code_=subprocess.call(shlex.split(_command_))
    _response_code_=0
    print("Execution shell %s",_command_)
    if _response_code_ == 0:
        return 0
    else:
        return _response_code_


def executeStep(stepName, step):
    logging.info("Starting the step execution %s",stepName)
    _task_type_=step['TYPE']
    _resource_name_=step['RESOURCE']
    _parameters_=step['PARAMETER']
    _retries=step['RETRIES']
    _waitime=step['WAITTIME']
    _parameter_flag_=step['PARAMETERFLAG']
    _retry_count_=0
    _run_command_=''
    if _task_type_ == 'ECS':
        logging.info('Decoding the parameter for the ECS task execution')
        _ecs_run_file_loc='/home/jjayabal/Autosys/lib/execute-ecs-task.sh'
        _ecs_task_definition_='ddl-'+runtime_environment+'-'+_resource_name_
        if _parameter_flag_ :
            _entry_commands_=_parameters_['COMMANDS']
            _envi_vars_=_parameters_['ENVIRONMENT']
            _run_command_=_ecs_run_file_loc+' '+runtime_environment+' '+_ecs_task_definition_+' us-east-1 true '+_envi_vars_+' '+_entry_commands_
        else:
            _run_command_=_ecs_run_file_loc+' '+runtime_environment+' '+_ecs_task_definition_+' us-east-1 false'
        
    elif _task_type_ == 'GLUE':
        logging.info('Decoding the parameter for the GLUE execution')
        _glue_run_file_loc='/home/jjayabal/Autosys/lib/execute-glue.sh'
        _glue_job_name_='ddl-'+runtime_environment+'-pipe1-gluejob-'+_resource_name_
        print(_glue_job_name_)
        _run_command_=_glue_run_file_loc+' '+runtime_environment+' '+_resource_name_+' us-east-1'
    
    
    _execution_status_=True
    while _execution_status_ and _retry_count_ <= _retries:
        _response_code_=runShell(_run_command_)
        if _response_code_ == 0:
            logging.info('Step %s execution completed successfully',stepName)
            _execution_status_=False
        else:
            logging.info('Step %s execution Failed', stepName)
            logging.info('Waiting for %i sec to retry',_waitime)
            time.sleep(_waitime)
            _retry_count_ += 1
            if _retry_count_ <= _retries:
                logging.info('Retrying %i of %i',_retry_count_,_retries)
    if _execution_status_:
        logging.error('Step %s execution failed. Error Code %s',stepName,_response_code_)
        return _response_code_
    else:
        return _response_code_


def main():
    executeFlow('IPIS_REPORT')

if __name__== "__main__":
    main()