from .term import Term, run_remote_cmd


def restart_dagit_service(cfg):
    Term.waiting('Restarting dagit systemd service...')
    retval = run_remote_cmd(cfg.key_file_path, cfg.remote_host, 'sudo systemctl restart dagit')
    Term.rewind()
    if retval == 0:
        Term.rewind()
        Term.success('Service restarted')
    else:
        Term.rewind()
        Term.fatal('Could not restart dagit service')


def start_dagit_service(cfg):
    Term.waiting('Starting dagit systemd service...')
    retval = run_remote_cmd(cfg.key_file_path, cfg.remote_host, 'sudo systemctl start dagit')
    Term.rewind()
    if retval == 0:
        Term.rewind()
        Term.success('Service started')
    else:
        Term.rewind()
        Term.fatal('Could not start dagit service')


def stop_dagit_service(cfg):
    Term.waiting('Stopping dagit systemd service...')
    retval = run_remote_cmd(cfg.key_file_path, cfg.remote_host, 'sudo systemctl stop dagit')
    Term.rewind()
    if retval == 0:
        Term.rewind()
        Term.success('Service stopped')
    else:
        Term.rewind()
        Term.fatal('Could not stop dagit service')
