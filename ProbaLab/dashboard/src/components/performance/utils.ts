export function wilsonInterval(correct: number, total: number, z: number = 1.96): [number, number] {
    if (total === 0) return [0, 0]
    const p = correct / total
    const denominator = 1 + z * z / total
    const center = (p + z * z / (2 * total)) / denominator
    const margin = (z * Math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))) / denominator
    return [Math.max(0, (center - margin) * 100), Math.min(100, (center + margin) * 100)]
}

export function formatWilson(accuracy: number, total: number): string {
    if (total === 0) return `${accuracy}%`
    const correct = Math.round(accuracy * total / 100)
    const [lo, hi] = wilsonInterval(correct, total)
    const margin = (hi - lo) / 2
    return `${accuracy}% (±${margin.toFixed(1)}%)`
}
