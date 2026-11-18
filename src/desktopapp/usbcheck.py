"""Read-only USB soak test over the camera's program files; never stages native workers.

The two program files are the same large reads a real write performs during its
full readback. Every round re-reads both and must match the first round byte for
byte. The clock starts once the service connection is ready, so connection and
authentication time never counts towards the minimum duration. A completed read
slower than MIN_MB_PER_SECOND indicates a degraded link (USB 1.1, hub or poor
cable); a read that hangs is stopped by the transport's own timeout and fails.
"""
import time
from pathlib import Path
from .paths import write_json

PATHS=('/usr/lib/appFw.so','/cp/cpapp-b.bin')
MIN_SECONDS=120
MIN_ROUNDS=5
MAX_ROUNDS=60
MIN_MB_PER_SECOND=2.0
MIN_BYTES,MAX_BYTES=1024*1024,256*1024*1024
NOTE='A pass only shows that continuous read-only transfers were stable during this period; it does not guarantee the connection will not drop while flashing, and it is not a cable certification.'


class Incomplete(RuntimeError):
    """The round cap was reached before the minimum duration; not a pass."""


def run(job,*,factory=None,clock=time.monotonic,min_seconds=MIN_SECONDS,min_rounds=MIN_ROUNDS,
        max_rounds=MAX_ROUNDS,min_rate=MIN_MB_PER_SECOND):
    if factory is None:
        from looktool.devicesession import Camera
        factory=Camera
    job=Path(job);job.mkdir(parents=True,exist_ok=True)
    report=dict(schema='a7c2-usb-stability/3',phase='CONNECTING',paths=list(PATHS),rounds=[],
                minimum_seconds=min_seconds,minimum_rounds=min_rounds,maximum_rounds=max_rounds,
                minimum_mb_per_second=min_rate,camera_firmware_written=False,camera_settings_written=False,
                native_worker_executed=False,note=NOTE)
    def save():write_json(job/'usb-stability.private.json',report)
    save();connect_begin=clock();start=None;number=0
    def elapsed():return 0.0 if start is None else clock()-start
    try:
        with factory() as camera:
            start=clock();report.update(phase='READING',connect_seconds=round(start-connect_begin,3));save()
            baseline={}
            while number<min_rounds or elapsed()<min_seconds:
                if number>=max_rounds:
                    raise Incomplete('Read %d rounds and reached the round limit, but continuous reading lasted only %.0f s, less than %d s; this run does not count as a pass'%
                                     (number,elapsed(),min_seconds))
                number+=1
                print('USB stability check: round %d, read-only read of program files (at least %d rounds, %d s continuous); no firmware or settings are written.'%
                      (number,min_rounds,min_seconds),flush=True)
                reads=[]
                for path in PATHS:
                    begin=clock()
                    try:
                        raw=camera.read(path)
                        seconds=clock()-begin
                        if raw is None or not MIN_BYTES<=len(raw)<=MAX_BYTES:
                            raise ValueError('Program file was not fully read back: '+path)
                        if path in baseline and raw!=baseline[path]:
                            raise ValueError('Repeated readback returned different bytes: '+path)
                        rate=len(raw)/1048576/seconds if seconds>0 else None
                        if rate is not None and rate<min_rate:
                            raise ValueError('Reading %s ran at only %.2f MB/s, below %.1f MB/s; the connection may go through USB 1.1, a hub, or a poor-quality cable'%
                                             (path,rate,min_rate))
                    except BaseException:
                        mark=getattr(camera,'mark_unknown',None)
                        if mark:mark()
                        raise
                    baseline.setdefault(path,raw)
                    reads.append(dict(path=path,bytes=len(raw),seconds=round(seconds,3),
                                      mb_per_second=round(rate,2) if rate is not None else None))
                report['rounds'].append(dict(round=number,bytes=sum(r['bytes'] for r in reads),reads=reads,passed=True))
                save()
            seconds=elapsed()
        speeds=[r['mb_per_second'] for row in report['rounds'] for r in row['reads'] if r['mb_per_second']]
        report.update(phase='PASSED',total_bytes=sum(r['bytes'] for r in report['rounds']),
                      seconds=round(seconds,3),camera_io_ended=True,
                      slowest_mb_per_second=min(speeds) if speeds else None,
                      fastest_mb_per_second=max(speeds) if speeds else None)
        save()
        print('All %d read-only rounds completed, %.1f MB in total, %.0f s of continuous reading, bytes identical in every round. %s'%
              (len(report['rounds']),report['total_bytes']/1048576,report['seconds'],NOTE),flush=True)
        return report
    except BaseException as exc:
        incomplete=isinstance(exc,Incomplete)
        connected=start is not None
        report.update(phase='INCOMPLETE' if incomplete else 'FAILED',
                      failed_stage='reading' if connected else 'connecting',
                      failed_round=number if connected and not incomplete else None,
                      error_type=type(exc).__name__,error=str(exc),camera_io_ended=True,seconds=round(elapsed(),3))
        save()
        if incomplete:
            raise RuntimeError('USB stability check incomplete: %s. No firmware or settings were written.'%str(exc)) from exc
        raise RuntimeError('USB stability check failed (%s): %s. Try another cable or connect directly to a computer USB port and test again; no firmware or settings were written.'%
                           ('round %d'%number if connected else 'connection stage',str(exc))) from exc
