import { ArrowUpRight, Coffee, Route } from "lucide-react";
import { moodPresets, type MoodPreset } from "../preset-config";

export function MoodCards({ onSelect }: { onSelect: (mood: MoodPreset) => void }) {
  return moodPresets.map((mood) => (
    <button key={mood.id} data-ui="mood-card" className="flex flex-col relative overflow-hidden rounded-[21px] py-[19px] px-4
                                text-left min-h-50.5 [transition:transform_0.2s] tablet:py-[17px]
                                tablet:px-[11px] mobile:min-h-[183px] mobile:py-[17px]
                                mobile:px-[15px] mobile:rounded-[18px] narrow:py-[15px] narrow:px-3
                                mobile-type:min-h-48.5 [&:hover]:[transform:translateY(-3px)]
                                [&_>_span:nth-child(2)]:relative [&_>_span:nth-child(2)]:mt-auto
                                [&_strong]:block [&_strong]:text-[12px] [&_strong]:font-extrabold
                                [&_strong]:leading-[1.4] tablet:[&_strong]:text-[11px]
                                mobile:[&_strong]:text-[11px] narrow:[&_strong]:text-[11px]
                                mobile-type:[&_strong]:text-[13px]
                                mobile-type:[&_strong]:leading-[1.4]
                                narrow-type:[&_strong]:text-[12px] [&_small]:block
                                [&_small]:text-[11px] [&_small]:mt-1.5
                                tablet:[&_small]:text-[11px] mobile:[&_small]:text-[11px]
                                mobile:[&_small]:mt-[5px] mobile-type:[&_small]:text-[11px]
                                mobile-type:[&_small]:leading-[1.6] [&_>_svg]:absolute
                                [&_>_svg]:right-3.5 [&_>_svg]:top-3.5
                                mobile:[&_>_svg]:size-4 mobile:[&_>_svg]:right-[13px]
                                mobile:[&_>_svg]:top-3.5 mobile-type:[&_>_svg]:top-[15px]
                                mobile-type:[&_>_svg]:right-3"
      style={{ background: mood.color }} onClick={() => onSelect(mood)}>
      {mood.illustration === "nature" ? <span
                                data-ui="mood-drawing nature-drawing"
                                className="h-25 w-full block relative mobile:h-22 [&_span]:absolute
                                  [&_span]:bg-[#89a889] [&_span]:rounded-[60%_60%_30%_30%]
                                  [&_span]:h-[65px] [&_span]:w-8.5 [&_span]:left-6 [&_span]:top-1.5
                                  [&_span]:[transform:rotate(-7deg)]
                                  [&_span]:[box-shadow:inset_-8px_-3px_0_#557d7220]
                                  [&_span::after]:[content:''] [&_span::after]:absolute
                                  [&_span::after]:w-[3px] [&_span::after]:h-[39px]
                                  [&_span::after]:bg-[#697e60] [&_span::after]:-bottom-3
                                  [&_span::after]:left-4 [&_span::after]:rounded-[3px]
                                  [&_span:nth-child(2)]:left-[59px] [&_span:nth-child(2)]:top-4.5
                                  [&_span:nth-child(2)]:h-[47px] [&_span:nth-child(2)]:w-7.5
                                  [&_span:nth-child(2)]:bg-[#adc096]
                                  [&_span:nth-child(2)]:[transform:rotate(10deg)]
                                  [&_span:nth-child(3)]:left-[9px] [&_span:nth-child(3)]:top-[47px]
                                  [&_span:nth-child(3)]:h-4.5 [&_span:nth-child(3)]:w-19.5
                                  [&_span:nth-child(3)]:bg-[#d8e3ce]
                                  [&_span:nth-child(3)]:rounded-[50%]
                                  [&_span:nth-child(3)]:[transform:rotate(0)]
                                  [&_span:nth-child(3)]:z-0 [&_span:nth-child(3)::after]:hidden"
                              >
                                <span />
                                <span />
                                <span />
                              </span> : mood.illustration === "city" ? <span
                                data-ui="mood-drawing city-drawing"
                                className="h-25 w-full block relative mobile:h-22 [&_span]:h-12.5
                                  [&_span]:w-[33px] [&_span]:bg-[#cf9982] [&_span]:absolute
                                  [&_span]:left-[21px] [&_span]:top-[27px] [&_span]:rounded-[3px]
                                  [&_span]:[box-shadow:inset_-7px_0_0_#aa6c6015]
                                  [&_span::before]:[content:''] [&_span::before]:absolute
                                  [&_span::before]:[border-left:22px_solid_transparent]
                                  [&_span::before]:[border-right:22px_solid_transparent]
                                  [&_span::before]:[border-bottom:23px_solid_#b46e5a]
                                  [&_span::before]:left-[-5px] [&_span::before]:-top-5
                                  [&_span::after]:[content:''] [&_span::after]:absolute
                                  [&_span::after]:bg-[#fff4d9] [&_span::after]:left-2.5
                                  [&_span::after]:top-[13px] [&_span::after]:w-[7px]
                                  [&_span::after]:h-[11px] [&_span::after]:rounded-[5px_5px_0_0]
                                  [&_span::after]:[box-shadow:12px_0_0_#fff4d9,_0_19px_0_#fff4d9]
                                  [&_span:nth-child(2)]:left-15 [&_span:nth-child(2)]:top-[15px]
                                  [&_span:nth-child(2)]:h-[61px] [&_span:nth-child(2)]:w-6
                                  [&_span:nth-child(2)]:bg-[#e3bb93]
                                  [&_span:nth-child(2)::before]:[border-left-width:16px]
                                  [&_span:nth-child(2)::before]:[border-right-width:16px]
                                  [&_span:nth-child(2)::before]:[border-bottom-color:#75949e]
                                  [&_span:nth-child(2)::before]:-left-1
                                  [&_span:nth-child(2)::after]:left-2
                                  [&_span:nth-child(2)::after]:[box-shadow:0_19px_0_#fff4d9]
                                  [&_span:nth-child(3)]:h-[5px] [&_span:nth-child(3)]:w-[85px]
                                  [&_span:nth-child(3)]:bg-[#e7cabb] [&_span:nth-child(3)]:left-2.5
                                  [&_span:nth-child(3)]:top-19.5 [&_span:nth-child(3)]:rounded-[50%]
                                  [&_span:nth-child(3)::before]:hidden
                                  [&_span:nth-child(3)::after]:hidden"
                              >
                                <span />
                                <span />
                                <span />
                              </span> : (
        <span className="h-25 mobile:h-22 flex items-center pl-3" aria-hidden="true">
          {mood.illustration === "coffee" ? <Coffee size={65} strokeWidth={1.25} style={{ color: mood.ink }} /> : <Route size={65} strokeWidth={1.25} style={{ color: mood.ink }} />}
        </span>
      )}
      <span><strong>{mood.title}</strong><small style={{ color: mood.ink }}>{mood.subtitle}</small></span>
      <ArrowUpRight size={18} style={{ color: mood.ink }} />
    </button>
  ));
}
