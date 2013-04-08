from openerp.osv import osv, fields
from openerp import netsvc, pooler, SUPERUSER_ID
import logging
import time
import threading

_logger = logging.getLogger(__name__)


class Job(osv.Model):
    """ A simple queue to store a local or remote showroom action.
    Similar to ir.cron, but designed to run jobs as soon as possible,
    possibly in parallel.
    """
    _name = 'showroom.job'
    _description = 'Asynchronous job'

    _columns = {
        'active': fields.boolean('Active'),
        'name': fields.char(
            'Name',
            size=60,
            required=True),
        'model': fields.char(
            'Model',
            size=60,
            required=True),
        'function': fields.char(
            'Function',
            size=60,
            required=True),
        'kwargs': fields.serialized(
            'Params'),
        'host_id': fields.many2one(
            'showroom.server',
            'Server',
            help='Server on which the job runs'),
        'res_id': fields.integer(
            'Resource id',
            required=True),
        'state': fields.selection([
            ('running', 'Running'),
            ('success', 'Succeeded'),
            ('failure', 'Failed'),
            ('pending', 'Pending')],
            'Job state',
            required=True),
        'start_date': fields.datetime('Start date'),
        'end_date': fields.datetime('End date'),
        'user_id': fields.many2one('res.users', 'User'),
        'success_signal': fields.char(
            'Success signal',
            size=32,
            help='The workflow signal to send in case of success'),
        'failure_signal': fields.char(
            'Failure signal',
            size=32,
            help='the workflow signal to send in case of failure'),
    }

    _defaults = {
        'active': True,
        'state': 'pending',
        'user_id': lambda self, cr, uid, context: uid,
    }

    def _clean_old_jobs(self, cr):
        """ disable jobs older than N seconds
        """
        seconds = self.pool.get('ir.config_parameter').get_param(
            cr, SUPERUSER_ID, 'showroom.job_max_age')
        query = ("SELECT id FROM " + self._table + " WHERE"
                 " COALESCE(write_date, create_date, (now() at time zone 'UTC'))::timestamp"
                 " < ((now() at time zone 'UTC') - interval %s)")
        cr.execute(query, ("%s seconds" % seconds,))
        ids = [x[0] for x in cr.fetchall()]
        self.write(cr, SUPERUSER_ID, ids, {'active': False})

    def _process_queue(self, cr, uid, context=None):
        """ Process the job queue in the right order
        """
        # check for running jobs
        max_jobs = self.pool.get('ir.config_parameter').get_param(cr, uid, 'showroom.max_jobs')
        job_ids = self.search(cr, uid, [('state', '=', 'running')], order='create_date')
        if len(job_ids) >= int(max_jobs):
            _logger.info('Maximum of %s simultaneous jobs already running.' % max_jobs)
            return cr.close()  # do nothing for now XXX check old jobs

        # Run the next job
        job_ids = self.search(cr, uid, [('state', '=', 'pending')], order='create_date', limit=1)
        for job in self.browse(cr, uid, job_ids, context):
            _logger.info('Selected job to run: id %s' % job.id)
            threaded_job = threading.Thread(
                target=self._run,
                args=(cr.dbname, uid, job.id,))
            threaded_job.start()
        if not job_ids:
            _logger.info('No more jobs to launch')

        cr.close()

    def create(self, cr, uid, values, context=None):
        """ Create a job and launch the processing
        """
        # don't use the same cursor and write immediately
        dbname = cr.dbname
        del cr
        cr = pooler.get_db(dbname).cursor()
        self._clean_old_jobs(cr)
        job_id = super(Job, self).create(cr, uid, values, context)
        cr.commit()
        self._process_queue(cr, uid)
        return job_id

    def _run(self, dbname, uid, job_id):
        """ Run the job thread, then continue to process the queue.
        """
        # tell we are running
        cr = pooler.get_db(dbname).cursor()
        job_values = self.read(cr, uid, job_id, [], load='_classic_write')
        self.write(cr, uid, job_id, {
            'state': 'running',
            'start_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        cr.commit()
        cr.close()

        # run the function
        _logger.info('Starting job id %s: %s )...' % (job_id, job_values))
        cr = pooler.get_db(dbname).cursor()
        res_id = job_values['res_id']
        model = job_values['model']
        function = job_values['function']
        kwargs = job_values['kwargs']
        try:
            getattr(self.pool.get(model), function)(cr, uid, [res_id], **kwargs)
        except Exception, e:
            # send the failure signal with another cursor, then raise
            cr2 = pooler.get_db(dbname).cursor()
            self.write(cr2, uid, job_id, {
                'state': 'failure',
                'end_date': time.strftime('%Y-%m-%d %H:%M:%S')})
            wf_service = netsvc.LocalService("workflow")
            if job_values['failure_signal']:
                wf_service.trg_validate(uid, model,
                                        res_id,
                                        job_values['failure_signal'],
                                        cr2)
            self.pool.get(model).message_post(cr2, uid, [res_id], body=e.message, type='notification')
            # TODO add a cron tu purge jobs at startup
            cr2.commit()
            cr2.close()
            _logger.exception('Finished job %s with failure: %s' % (job_id, e.message))
        else:
            # tell we have finished and send the signal if any
            self.write(cr, uid, job_id, {
                'state': 'success',
                'end_date': time.strftime('%Y-%m-%d %H:%M:%S')})
            if job_values['success_signal']:
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_validate(uid, model,
                                        job_values['res_id'],
                                        job_values['success_signal'],
                                        cr)
            _logger.info('Finished job %s with success...' % job_id)
            cr.commit()
        self._process_queue(cr, uid)
