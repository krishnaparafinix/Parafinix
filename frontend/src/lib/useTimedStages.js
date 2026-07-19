import { useEffect, useRef, useState } from 'react'

// The backend runs report generation as a single blocking call (3 drafting
// passes + a compliance check), so there is no real server-sent progress.
// This advances a stage index on a timer, calibrated to each pass's rough
// duration, purely so the UI doesn't sit on a bare spinner for ~90s+.
export function useTimedStages(active, stageDurationsMs) {
  const [index, setIndex] = useState(0)
  const timeouts = useRef([])

  useEffect(() => {
    timeouts.current.forEach(clearTimeout)
    timeouts.current = []
    if (!active) {
      setIndex(0)
      return
    }
    let elapsed = 0
    stageDurationsMs.forEach((duration, i) => {
      if (i === 0) return
      elapsed += stageDurationsMs[i - 1]
      const t = setTimeout(() => setIndex(i), elapsed)
      timeouts.current.push(t)
    })
    return () => timeouts.current.forEach(clearTimeout)
  }, [active])

  return index
}
