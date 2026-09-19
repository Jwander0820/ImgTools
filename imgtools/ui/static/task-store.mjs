const terminal = job => ['completed', 'failed', 'cancelled'].includes(job.status);

export function createTaskStore({request, onChange = () => {}, onResult = () => {}}) {
  let jobs = [];
  let pending = null;
  let submitting = false;
  let uncertain = false;
  let error = '';
  let sessionId;
  let ready = false;
  let revision = 0;
  let refreshSequence = 0;
  const delivered = new Set();
  const snapshot = () => ({jobs, submitting, uncertain, error, ready});
  const notify = () => onChange(snapshot());
  const busy = action => Boolean(pending?.action === action || jobs.some(job => job.action === action && !terminal(job)));
  async function send() {
    revision += 1;
    submitting = true; error = ''; notify();
    try {
      const {job} = await request('/api/jobs', pending);
      jobs = [job, ...jobs.filter(item => item.id !== job.id)];
      pending = null; uncertain = false;
      return job;
    } catch (err) {
      // A transport failure may happen after the server accepts a job.
      // Preserve the exact request ID until the same request is retried.
      uncertain = !err.rejected;
      if (err.rejected) pending = null;
      error = err.message;
      throw err;
    } finally {
      revision += 1;
      submitting = false; notify();
    }
  }
  return {
    snapshot, busy,
    async submit(action, params) {
      if (pending || busy(action)) throw Error('這個工具已有任務，請等待完成或先取消');
      pending = {action, params: structuredClone(params), request_id: crypto.randomUUID(), ...(sessionId ? {session_id:sessionId} : {})};
      return send();
    },
    async retrySubmission() {
      if (!pending || submitting) return;
      return send();
    },
    async refresh() {
      const startedAt = revision;
      const sequence = ++refreshSequence;
      const current = () => startedAt === revision && sequence === refreshSequence;
      try {
        const data = await request('/api/jobs');
        if (!current()) return;
        jobs = data.jobs;
        sessionId = data.session_id;
        ready = true;
        error = ''; notify();
        const completed = jobs.filter(job => terminal(job) && (job.result || job.has_result) && !delivered.has(job.id));
        if (completed.length) {
          const job = completed[0].result ? completed[0] : (await request(`/api/jobs/${completed[0].id}`)).job;
          if (!current()) return;
          completed.forEach(item => delivered.add(item.id));
          onResult(job);
        }
      } catch (err) {
        if (!current()) return;
        error = `暫時無法取得任務狀態：${err.message}`;
        notify(); throw err;
      }
    },
    async getResult(id) { return (await request(`/api/jobs/${id}`)).job; },
    async cancel(id) {
      revision += 1;
      try {
        const {job} = await request('/api/jobs/cancel', {job_id: id});
        jobs = jobs.map(item => item.id === id ? job : item); notify();
      } finally { revision += 1; }
      await this.refresh();
    },
  };
}
