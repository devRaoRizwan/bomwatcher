import { useCallback, useEffect, useRef, useState } from 'react'

export function useAsync(loader, key, { pollWhile, interval = 3000 } = {}) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const loaderRef = useRef(loader)
  const pollRef = useRef(pollWhile)

  useEffect(() => {
    loaderRef.current = loader
    pollRef.current = pollWhile
  })

  const reload = useCallback(async (silent = false) => {
    if (!silent) setState((s) => ({ ...s, loading: true }))
    try {
      const data = await loaderRef.current()
      setState({ data, error: null, loading: false })
      return data
    } catch (error) {
      setState((s) => ({ ...s, error, loading: false }))
    }
  }, [])

  useEffect(() => {
    let timer
    let cancelled = false
    const run = async (silent) => {
      const data = await reload(silent)
      if (!cancelled && pollRef.current?.(data)) timer = setTimeout(() => run(true), interval)
    }
    run(false)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [key, reload, interval])

  return { ...state, reload }
}
