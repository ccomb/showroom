from openerp.osv import osv, fields
import logging
import time
import pooler
import threading
_logger = logging.getLogger(__name__)


class Queue(osv.Model):
    """ A simple queue to store a local or remote showroom action.
    """
    _name = 'showroom.queue'

    _columns = {
        'active': fields.boolean('Currently running'),
        'name': fields.char(
            'Name',
            size=60,
            required=True),
        'script': fields.char(
            'Script',
            size=60),
        'params': fields.char(
            'Params',
            size=128),
        'host_id': fields.many2one(
            'showroom.server',
            'Server',
            help='Server on which the job runs'),
        'template_id': fields.many2one(
            'showroom.template',
            'Template',
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'running': fields.boolean('Currently running'),
        'start_date': fields.datetime('Start date'),
        'end_date': fields.datetime('End date'),
        'user_id': fields.many2one('res.users', 'User'),
    }

    _defaults = {
        'active': True,
        'user_id': lambda self, cr, uid, context: uid,
    }

    def _process_queue(self, cr, uid, context=None):
        """ Process the job queue in the right order
        """
        # check for running jobs
        max_jobs = self.pool.get('ir.config_parameter').get_param(cr, uid, 'showroom.max_jobs')
        job_ids = self.search(cr, uid, [('running', '=', True)], order='create_date')
        if len(job_ids) >= int(max_jobs):
            _logger.info('Maximum of %s simultaneous jobs already running.' % max_jobs)
            return cr.close()  # do nothing for now XXX check old jobs

        # Run the next job
        job_ids = self.search(cr, uid, [('running', '=', False)], order='create_date', limit=1)
        for job in self.browse(cr, uid, job_ids, context):
            _logger.info('Selected job to run: id %s' % job.id)
            threaded_job = threading.Thread(
                target=self._run,
                args=(cr.dbname, uid, job.id,))
            threaded_job.start()
        if not job_ids:
            _logger.info('(No more jobs to launch)')

        cr.close()

    def create(self, cr, uid, values, context=None):
        """ Create a job and launch the processing
        """
        # don't use the same cursor and write immediately
        dbname = cr.dbname
        del cr
        cr = pooler.get_db(dbname).cursor()
        job_id = super(Queue, self).create(cr, uid, values, context)
        cr.commit()
        self._process_queue(cr, uid)
        return job_id

    def _run(self, dbname, uid, job_id):
        """ Run the job thread, then continue to process the queue.
        """
        # tell we are running
        cr = pooler.get_db(dbname).cursor()
        job_values = self.read(cr, uid, job_id, [
            'id', 'name', 'script', 'params', 'host_id'])
        self.write(cr, uid, job_id, {
            'running': True,
            'start_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        cr.commit()
        cr.close()

        # run the script
        _logger.info('Starting job id %s: %s )...' % (job_id, job_values))
        time.sleep(20)

        # tell we have finished
        cr = pooler.get_db(dbname).cursor()
        self.write(cr, uid, job_id, {
            'running': False,
            'end_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'active': False})
        cr.commit()
        _logger.info('Finished job %s...' % job_id)
        self._process_queue(cr, uid)



