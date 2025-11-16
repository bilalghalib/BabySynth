import type { LaunchpadConfig } from '@/types'
import { babyConfig } from './baby'
import { partyConfig } from './party'
import { bedtimeConfig } from './bedtime'
import { learningConfig } from './learning'
import { drumsConfig } from './drums'

export const allConfigs: LaunchpadConfig[] = [
  babyConfig,
  partyConfig,
  bedtimeConfig,
  learningConfig,
  drumsConfig,
]

export const configMap: Record<string, LaunchpadConfig> = {
  baby: babyConfig,
  party: partyConfig,
  bedtime: bedtimeConfig,
  learning: learningConfig,
  drums: drumsConfig,
}

export {
  babyConfig,
  partyConfig,
  bedtimeConfig,
  learningConfig,
  drumsConfig,
}

export function getConfig(name: string): LaunchpadConfig | undefined {
  return configMap[name.toLowerCase()]
}
