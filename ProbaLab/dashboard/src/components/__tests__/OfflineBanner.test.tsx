import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import OfflineBanner from '../OfflineBanner'

// jsdom defaults navigator.onLine to true, so we control it per test.
function setOnline(value: boolean) {
  Object.defineProperty(navigator, 'onLine', {
    configurable: true,
    get: () => value,
  })
}

describe('OfflineBanner', () => {
  afterEach(() => {
    // Restore online state after each test.
    setOnline(true)
  })

  it('renders nothing when the browser is online', () => {
    setOnline(true)
    const { container } = render(<OfflineBanner />)
    expect(container.firstChild).toBeNull()
  })

  it('renders the banner when the browser starts offline', () => {
    setOnline(false)
    render(<OfflineBanner />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Connexion perdue')
  })

  it('shows the banner after the browser goes offline', () => {
    setOnline(true)
    render(<OfflineBanner />)
    // Initially hidden — no alert element
    expect(screen.queryByRole('alert')).toBeNull()

    act(() => {
      window.dispatchEvent(new Event('offline'))
    })

    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('hides the banner after the browser comes back online', () => {
    setOnline(false)
    render(<OfflineBanner />)
    expect(screen.getByRole('alert')).toBeInTheDocument()

    act(() => {
      setOnline(true)
      window.dispatchEvent(new Event('online'))
    })

    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('cleans up event listeners on unmount', () => {
    const addSpy = vi.spyOn(window, 'addEventListener')
    const removeSpy = vi.spyOn(window, 'removeEventListener')

    setOnline(true)
    const { unmount } = render(<OfflineBanner />)
    unmount()

    const offlineRemoved = removeSpy.mock.calls.some(([event]) => event === 'offline')
    const onlineRemoved = removeSpy.mock.calls.some(([event]) => event === 'online')
    expect(offlineRemoved).toBe(true)
    expect(onlineRemoved).toBe(true)

    addSpy.mockRestore()
    removeSpy.mockRestore()
  })
})
