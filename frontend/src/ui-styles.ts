/** Shared Tailwind recipes for repeated primitives and interactive states. */

export const appHeaderStyles = [
  "max-w-[1120px] h-[100px] m-auto flex items-center justify-between",
  "[border-bottom:1px_solid_var(--line)] desktop-fit:mx-[35px] mobile:h-[76px] mobile:my-0",
  "mobile:mx-[22px] mobile:[border:0] mobile:pt-[env(safe-area-inset-top)] narrow:my-0 narrow:mx-[17px]",
  "mobile-spacing:mx-[24px] narrow-spacing:mx-[20px] short:h-[64px] short:min-h-[64px] short:shrink-0",
  "mobile:[[data-ui~=screen-wizard]_&]:hidden mobile:[[data-ui~=screen-result]_&]:hidden",
  "[[data-ui~=screen-preset]_&]:hidden [[data-ui~=screen-loading]_&]:w-[calc(100%_-_48px)]",
  "[[data-ui~=screen-loading]_&]:my-0 [[data-ui~=screen-loading]_&]:mx-auto",
  "[[data-ui~=screen-loading]_&]:shrink-0",
  "loading-narrow:[[data-ui~=screen-loading]_&]:w-[calc(100%_-_40px)]",
].join(" ");

export const appMainStyles = [
  "max-w-[1120px] m-auto py-[24px] px-0 desktop-fit:mx-[35px] mobile:m-0 mobile:pt-[16px]",
  "mobile:px-[24px] mobile:pb-[24px] narrow:px-[17px] narrow-spacing:px-[20px] short:pt-[16px]",
  "mobile:[[data-ui~=screen-wizard]_&]:p-0 narrow-spacing:[[data-ui~=screen-wizard]_&]:p-0",
  "mobile:[[data-ui~=screen-result]_&]:pt-0 mobile:[[data-ui~=screen-result]_&]:px-[24px]",
  "mobile:[[data-ui~=screen-result]_&]:pb-[calc(92px_+_env(safe-area-inset-bottom))]",
  "narrow:[[data-ui~=screen-result]_&]:px-[17px] desktop-result:[[data-ui~=screen-result]_&]:pb-[104px]",
  "narrow-spacing:[[data-ui~=screen-result]_&]:px-[20px] [[data-ui~=screen-preset]_&]:pt-0",
  "[[data-ui~=screen-preset]_&]:pb-[calc(136px_+_env(safe-area-inset-bottom))]",
  "preset-mobile:[[data-ui~=screen-preset]_&]:pb-[calc(110px_+_env(safe-area-inset-bottom))]",
  "[[data-ui~=screen-loading]_&]:[flex:1] [[data-ui~=screen-loading]_&]:flex",
  "[[data-ui~=screen-loading]_&]:items-center [[data-ui~=screen-loading]_&]:w-full",
  "[[data-ui~=screen-loading]_&]:my-0 [[data-ui~=screen-loading]_&]:mx-auto",
  "[[data-ui~=screen-loading]_&]:pt-[8px]",
  "[[data-ui~=screen-loading]_&]:pb-[max(12px,_env(safe-area-inset-bottom))]",
].join(" ");

export const emptyStateStyles = [
  "flex flex-col items-center justify-center py-[45px] px-[20px] text-center max-w-[490px] m-auto",
  "min-h-[370px] mobile:min-h-[390px] mobile:py-[30px] mobile:px-[10px] [&_h1]:text-[28px]",
  "[&_h1]:tracking-[-1px] [&_h1]:mt-[20px] [&_h1]:mx-0 [&_h1]:mb-[10px] [&_h2]:text-[22px]",
  "[&_h2]:[font-weight:750] [&_h2]:tracking-[-0.7px] mobile:[&_h2]:text-[21px] [&_p]:text-[#959eb1]",
  "[&_p]:text-[12px] [&_p]:leading-[1.9] [&_p]:mt-[14px] [&_p]:mx-0 [&_p]:mb-[25px] [&_p]:max-w-[320px]",
  "mobile:[&_p]:text-[11px] mobile:[&_p]:max-w-[280px] mobile-type:[&_p]:text-[14px]",
  "[[data-ui~=trips-page]_&]:min-h-0 [[data-ui~=trips-page]_&]:pt-[12px]",
  "[[data-ui~=trips-page]_&]:px-[8px] [[data-ui~=trips-page]_&]:pb-[16px]",
  "[[data-ui~=trips-page]_&_p]:mt-[12px] [[data-ui~=trips-page]_&_p]:mx-0",
  "[[data-ui~=trips-page]_&_p]:mb-[20px] [[data-ui~=trips-page]_&_p]:leading-[1.7]",
].join(" ");

export const textButtonStyles = [
  "inline-flex items-center justify-center gap-[8px] text-[12px] [font-weight:650]",
  "[background:transparent] text-brand py-[10px] px-[4px] [[data-ui~=onboarding-header]_&]:text-[12px]",
  "mobile:[[data-ui~=onboarding-header]_&]:text-[11px] [[data-ui~=result-hero]_>_&]:text-[11px]",
  "[[data-ui~=result-hero]_>_&]:min-h-[38px] mobile:[[data-ui~=result-hero]_>_&]:text-[11px]",
  "[[data-ui~=train-bottom]_>_&]:text-[11px]",
  "mobile:[[data-ui~=train-bottom]_>_&]:text-[11px]",
  "mobile-type:[[data-ui~=train-bottom]_>_&]:text-[12px]",
].join(" ");

export const avatarStyles = [
  "h-[40px] w-[40px] min-h-[40px] [background:#e9edff] text-brand [border:1px_solid_#dce2ff] grid",
  "place-items-center rounded-[50%] font-bold p-0 shrink-0 mobile:h-[36px] mobile:w-[36px]",
  "mobile:min-h-[36px] overflow-hidden [&_>_img]:w-full [&_>_img]:h-full [&_>_img]:object-cover",
  "[&_>_img]:rounded-[inherit]",
].join(" ");

export const eyebrowStyles = [
  "block text-[11px] font-extrabold tracking-[1.4px] text-muted mobile:text-[11px]",
  "mobile:tracking-[1.05px] mobile-type:text-[10px] [[data-ui~=onboarding-copy]_&]:text-[11px]",
  "[[data-ui~=onboarding-copy]_&]:text-brand [[data-ui~=onboarding-copy]_&]:tracking-[1.8px]",
  "mobile:[[data-ui~=onboarding-copy]_&]:text-[11px]",
  "mobile:[[data-ui~=onboarding-copy]_&]:tracking-[1.5px] [[data-ui~=step-heading]_&]:text-[11px]",
  "[[data-ui~=step-heading]_&]:tracking-[1.5px] [[data-ui~=step-heading]_&]:text-[#a2a7b7]",
  "mobile:[[data-ui~=step-heading]_&]:text-[11px] [[data-ui~=loading-page]_&]:text-[11px]",
  "[[data-ui~=loading-page]_&]:tracking-[1.4px] [[data-ui~=loading-page]_&]:text-[#8b95ae]",
  "[[data-ui~=budget-panel]_>_&]:text-[11px] [[data-ui~=budget-panel]_>_&]:tracking-[1px]",
  "mobile:[[data-ui~=budget-panel]_>_&]:text-[11px] mobile:[[data-ui~=loading-page]_>_&]:text-[11px]",
  "mobile:[[data-ui~=loading-page]_>_&]:tracking-[1.2px] narrow:[[data-ui~=home-heading]_&]:text-[11px]",
  "[[data-ui~=preset-section]_&]:text-brand [[data-ui~=preset-section]_&]:mb-[8px]",
  "[[data-ui~=preset-section]_&]:text-[10px] [[data-ui~=preset-intro]_&]:text-brand",
  "[[data-ui~=preset-intro]_&]:tracking-[0.6px]",
].join(" ");

export const sectionHeadingStyles = [
  "flex justify-between items-baseline mb-[17px] gap-[10px] mobile:mb-[14px] mobile-type:items-start",
  "mobile-type:gap-[10px] [&_h2]:text-[18px] [&_h2]:tracking-[-0.55px] [&_h2]:font-extrabold",
  "mobile:[&_h2]:text-[15px] mobile:[&_h2]:tracking-[-0.5px] narrow:[&_h2]:text-[13px]",
  "[&_>_span]:text-[11px] [&_>_span]:text-muted mobile:[&_>_span]:text-[11px] mobile:[&_>_span]:m-0",
  "narrow:[&_>_span]:text-[11px] mobile-type:[&_>_span]:max-w-[100px] mobile-type:[&_>_span]:text-right",
  "mobile-type:[&_>_span]:leading-[1.6] [[data-ui~=home-side]_&]:flex [[data-ui~=home-side]_&]:flex-wrap",
  "[[data-ui~=home-side]_&]:gap-[4px_12px] [[data-ui~=home-side]_&]:items-baseline",
  "[[data-ui~=home-side]_&_>_span]:block [[data-ui~=home-side]_&_>_span]:mt-[5px]",
  "mobile:[[data-ui~=home-side]_&_>_span]:text-[11px] mobile:[[data-ui~=home-side]_&_>_span]:m-0",
  "narrow:[[data-ui~=home-side]_&_>_span]:text-[11px] [[data-ui~=home-side]_&_>_span]:max-w-[none]",
  "[[data-ui~=home-side]_&_>_span]:shrink-0 [[data-ui~=home-side]_&_>_span]:whitespace-nowrap",
  "[[data-ui~=home-side]_&_>_span]:text-left mobile:[[data-ui~=example-section]_>_&]:block",
  "mobile:[[data-ui~=example-section]_>_&_>_span]:block",
  "mobile:[[data-ui~=example-section]_>_&_>_span]:mt-[6px]",
  "mobile-type:[[data-ui~=example-section]_&_>_span]:max-w-[none]",
  "mobile-type:[[data-ui~=example-section]_&_>_span]:text-left",
  "[[data-ui~=preset-section]_&]:[align-items:end] preset-mobile:[[data-ui~=preset-section]_&]:flex-wrap",
  "preset-mobile:[[data-ui~=preset-section]_&]:gap-[8px] [[data-ui~=preset-section]_&_h2]:text-[23px]",
  "[[data-ui~=preset-section]_&_h2]:tracking-[-0.8px]",
  "preset-mobile:[[data-ui~=preset-section]_&_h2]:text-[20px]",
  "preset-mobile:[[data-ui~=preset-section]_&_>_span]:max-w-[none]",
  "preset-mobile:[[data-ui~=preset-section]_&_>_span]:text-left",
].join(" ");

export const tripsPageStyles = [
  "max-w-[690px] my-[12px] mx-auto mobile:my-[2px] mobile:mx-0 [&_>_h1]:text-[37px]",
  "[&_>_h1]:leading-[1.3] [&_>_h1]:tracking-[-1.4px] [&_>_h1]:font-extrabold [&_>_h1]:mt-[14px]",
  "[&_>_h1]:mx-0 [&_>_h1]:mb-[25px] mobile:[&_>_h1]:text-[29px] mobile:[&_>_h1]:tracking-[-1.1px]",
  "mobile:[&_>_h1]:mt-[12px] mobile:[&_>_h1]:mx-0 mobile:[&_>_h1]:mb-[22px]",
].join(" ");

export const activeStyles = [
  "[[data-ui~=bottom-nav]_button&]:text-brand",
  "[[data-ui~=wizard-aside]_li&]:text-ink",
  "[[data-ui~=wizard-aside]_li&]:[font-weight:750]",
  "[[data-ui~=wizard-aside]_li&_>_span]:[background:var(--blue)]",
  "[[data-ui~=wizard-aside]_li&_>_span]:text-[white]",
  "[[data-ui~=wizard-aside]_li&_>_span]:[border-color:var(--blue)]",
  "[[data-ui~=step-progress]_>_span&]:[background:var(--blue)]",
  "[[data-ui~=quick-chips]_button&]:[border-color:#cdd6ff]",
  "[[data-ui~=quick-chips]_button&]:[background:#f0f3ff] [[data-ui~=quick-chips]_button&]:text-brand",
  "[[data-ui~=segmented]_button&]:[background:white] [[data-ui~=segmented]_button&]:text-brand",
  "[[data-ui~=segmented]_button&]:[box-shadow:0_2px_5px_#26335308]",
  "[[data-ui~=segmented]_button&]:[font-weight:750] [[data-ui~=result-tabs]_>_button&]:text-brand",
  "[[data-ui~=result-tabs]_>_button&]:[font-weight:750]",
  "[[data-ui~=day-selector]_>_button&]:[background:#eaf0ff]",
  "[[data-ui~=day-selector]_>_button&]:[border-color:#aabaf6]",
  "[[data-ui~=day-selector]_>_button&]:text-brand",
].join(" ");

export const doneStyles = [
  "[[data-ui~=wizard-aside]_li&]:text-[#607ec7]",
  "[[data-ui~=wizard-aside]_li&_>_span]:[background:#e9edff]",
  "[[data-ui~=wizard-aside]_li&_>_span]:[border-color:#e0e6ff]",
  "[[data-ui~=wizard-aside]_li&_>_span]:text-brand [[data-ui~=generation-stages]_>_span&]:text-[#6677b6]",
].join(" ");

export const iconButtonStyles = [
  "w-[44px] h-[44px] min-h-[44px] rounded-[50%] inline-grid place-items-center [background:transparent]",
  "text-ink shrink-0 [&:hover]:[background:#edeff6] [[data-ui~=notice]_&]:w-[32px]",
  "[[data-ui~=notice]_&]:min-h-[32px] [[data-ui~=notice]_&]:h-[32px]",
  "mobile:[[data-ui~=wizard-top]_&]:[background:white]",
  "mobile:[[data-ui~=wizard-top]_&]:[border:1px_solid_#edf0f6] mobile:[[data-ui~=wizard-top]_&]:w-[39px]",
  "mobile:[[data-ui~=wizard-top]_&]:h-[39px] mobile:[[data-ui~=wizard-top]_&]:min-h-[39px]",
].join(" ");

export const presetInfoCardStyles = [
  "p-[22px] [background:#fff] [border:1px_solid_var(--line)] rounded-[22px] [&_>_h2]:text-[17px]",
  "[&_>_h2]:mt-[16px] [&_>_h2]:mx-0 [&_>_h2]:mb-[12px] [&_>_h2]:tracking-[-0.3px] [&_p]:text-[12px]",
  "[&_p]:leading-[1.8] [&_p]:text-[#687389] [&_small]:text-[12px] [&_small]:leading-[1.8]",
  "[&_small]:text-[#687389] [&_dl]:my-[16px] [&_dl]:mx-0 [&_dl]:py-[12px] [&_dl]:px-0",
  "[&_dl]:[border-block:1px_solid_var(--line)] [&_dl_>_div]:flex [&_dl_>_div]:justify-between",
  "[&_dl_>_div]:gap-[12px] [&_dl_>_div]:py-[7px] [&_dl_>_div]:px-0 [&_dl_>_div]:text-[12px]",
  "[&_dl_>_div]:leading-[1.5] [&_dd]:m-0 [&_dd]:whitespace-nowrap [&_dd]:[font-weight:750]",
].join(" ");

export const packingListStyles = [
  "grid grid-cols-[1fr_1fr] gap-[5px_10px] mt-[8px] mobile:gap-[4px_9px] mobile-type:grid-cols-[1fr]",
  "[&_label]:relative [&_label]:flex [&_label]:gap-[8px] [&_label]:items-center [&_label]:text-[11px]",
  "[&_label]:leading-[1.6] [&_label]:text-[#8e96a8] [&_label]:min-h-[36px] [&_label]:[cursor:pointer]",
  "mobile:[&_label]:text-[11px] mobile:[&_label]:min-h-[40px] mobile-type:[&_label]:text-[12px]",
  "mobile-type:[&_label]:min-h-[44px] [&_input]:absolute [&_input]:opacity-0 [&_input]:w-[20px]",
  "[&_input]:h-[20px] [&_input]:min-h-0 [&_input]:m-0 [[data-ui~=preset-info-card]_&]:flex",
  "[[data-ui~=preset-info-card]_&]:flex-col",
  "[[data-ui~=preset-info-card][data-ui~=preset-packing-card]_&]:mt-[6px]",
].join(" ");

export const packingCheckboxStyles = [
  "h-[18px] w-[18px] [border:1px_solid_#dfe4ef] rounded-[6px] grid place-items-center shrink-0",
  "[[data-ui~=packed]_>_&]:[background:var(--blue)] [[data-ui~=packed]_>_&]:[border-color:var(--blue)]",
  "[[data-ui~=packed]_>_&]:text-[white]",
  "[[data-ui~=packing-list]_input:focus-visible_+_&]:[outline:3px_solid_#a3b1ff]",
  "[[data-ui~=packing-list]_input:focus-visible_+_&]:[outline-offset:3px]",
].join(" ");

export const fieldLabelStyles = [
  "block text-[11px] [font-weight:750] leading-[1.6] mobile:text-[11px] mobile-type:text-[13px]",
  "[&_input]:mt-[9px] [&_input]:block [&_input]:w-full [&_input]:[border:1px_solid_#e6e9f0]",
  "[&_input]:[background:#fafbfe] [&_input]:rounded-[13px] [&_input]:p-[14px] [&_input]:text-[13px]",
  "[&_input]:text-ink [&_input]:min-h-[51px] mobile:[&_input]:text-[16px] mobile:[&_input]:min-h-[54px]",
  "mobile:[&_input]:[background:#fff] mobile:[&_input]:p-[14px] [&_textarea]:mt-[9px] [&_textarea]:block",
  "[&_textarea]:w-full [&_textarea]:[border:1px_solid_#e6e9f0] [&_textarea]:[background:#fafbfe]",
  "[&_textarea]:rounded-[13px] [&_textarea]:p-[14px] [&_textarea]:text-[13px] [&_textarea]:text-ink",
  "[&_textarea]:[resize:vertical] [&_textarea]:min-h-[92px] [&_textarea]:leading-[1.7]",
  "mobile:[&_textarea]:[background:#fff] mobile:[&_textarea]:p-[14px] mobile:[&_textarea]:text-[14px]",
  "mobile:[&_textarea]:min-h-[100px] [&_select]:mt-[9px] [&_select]:block [&_select]:w-full",
  "[&_select]:[border:1px_solid_#e6e9f0] [&_select]:[background:#fafbfe] [&_select]:rounded-[13px]",
  "[&_select]:p-[14px] [&_select]:text-[13px] [&_select]:text-ink [&_select]:min-h-[51px]",
  "mobile:[&_select]:text-[14px] mobile:[&_select]:min-h-[54px] mobile:[&_select]:[background:#fff]",
  "mobile:[&_select]:p-[14px] [&_input::placeholder]:text-[#a3a9b8] [&_input::placeholder]:text-[12px]",
  "mobile:[&_input::placeholder]:text-[12px] [&_textarea::placeholder]:text-[#a3a9b8]",
  "[&_textarea::placeholder]:text-[12px] mobile:[&_textarea::placeholder]:text-[12px]",
  "[[data-ui~=fields-pair]_&]:text-[11px] mobile:[[data-ui~=fields-pair]_&]:text-[11px]",
].join(" ");

export const inlineNoteStyles = [
  "flex gap-[10px] items-start text-[11px] leading-[1.8] text-[#929bae] [background:#f8f9fc]",
  "rounded-[12px] p-[13px] mt-[16px] mobile:text-[11px] mobile:[background:#f0f3fa] mobile:mt-[16px]",
  "mobile:p-[13px] mobile-type:text-[12px] [&_>_svg]:mt-[2px] [&_>_svg]:text-[#8993b0]",
  "mobile:[[data-ui~=budget-panel]_&]:text-[11px] mobile-type:[[data-ui~=budget-panel]_&]:text-[12px]",
].join(" ");

export const inputWithIconStyles = [
  "[&_input]:block [&_input]:w-full [&_input]:[border:1px_solid_#e6e9f0] [&_input]:[background:#fafbfe]",
  "[&_input]:rounded-[13px] [&_input]:py-[14px] [&_input]:pr-[14px] [&_input]:text-[13px]",
  "[&_input]:text-ink [&_input]:min-h-[51px] [&_input]:pl-[44px] mobile:[&_input]:text-[16px]",
  "mobile:[&_input]:min-h-[54px] mobile:[&_input]:[background:#fff] mobile:[&_input]:py-[14px]",
  "mobile:[&_input]:pr-[14px] mobile:[&_input]:pl-[44px] [&_select]:block [&_select]:w-full",
  "[&_select]:[border:1px_solid_#e6e9f0] [&_select]:[background:#fafbfe] [&_select]:rounded-[13px]",
  "[&_select]:py-0 [&_select]:h-[54px] [&_select]:leading-[20px] [&_select]:pr-[14px] [&_select]:text-[13px] [&_select]:text-ink",
  "[&_select]:min-h-[51px] [&_select]:pl-[44px] [&_select]:[appearance:none]",
  "[&_select]:[background-image:url(\"data:image/svg+xml,%3Csvg_xmlns='http://www.w3.org/2000/svg'_width='12'_height='12'_viewBox='0_0_24_24'_fill='none'_stroke='%237c8293'_stroke-width='2'%3E%3Cpath_d='m6_9_6_6_6-6'/%3E%3C/svg%3E\")]",
  "[&_select]:[background-repeat:no-repeat] [&_select]:[background-position:calc(100%_-_18px)_center]",
  "mobile:[&_select]:text-[14px] mobile:[&_select]:min-h-[54px] mobile:[&_select]:[background:#fff]",
  "mobile:[&_select]:py-0 [&_select]:h-[54px] [&_select]:leading-[20px] mobile:[&_select]:pr-[14px] mobile:[&_select]:pl-[44px] flex items-center",
  "relative mt-[9px] [&_>_svg]:absolute [&_>_svg]:left-[15px] [&_>_svg]:text-[#7b88b4]",
  "[&_>_svg]:pointer-events-none",
].join(" ");

export const softBlueIconStyles = [
  "w-[47px] h-[47px] grid place-items-center rounded-[15px] shrink-0 tablet:[[data-ui~=how-card]_&]:h-[37px]",
  "tablet:[[data-ui~=how-card]_&]:w-[37px] tablet:[[data-ui~=how-card]_&]:rounded-[12px]",
  "mobile:[[data-ui~=how-card]_&]:h-[38px] mobile:[[data-ui~=how-card]_&]:w-[38px]",
  "mobile:[[data-ui~=how-card]_&]:rounded-[12px] mobile:[[data-ui~=section-title]_&]:h-[39px]",
  "mobile:[[data-ui~=section-title]_&]:w-[39px] mobile:[[data-ui~=section-title]_&]:rounded-[13px]",
  "mobile:[[data-ui~=map-button]_&]:w-[37px] mobile:[[data-ui~=map-button]_&]:h-[37px]",
  "mobile:[[data-ui~=map-button]_&]:rounded-[12px] mobile:[[data-ui~=saved-trip]_>_&]:h-[38px]",
  "mobile:[[data-ui~=saved-trip]_>_&]:w-[38px] mobile:[[data-ui~=saved-trip]_>_&]:rounded-[12px]",
  "mobile:[[data-ui~=about-info]_&]:w-[37px] mobile:[[data-ui~=about-info]_&]:h-[37px]",
  "mobile:[[data-ui~=about-info]_&]:rounded-[12px] [[data-ui~=soft-icon]&]:[background:#ecf0ff]",
  "[[data-ui~=soft-icon]&]:text-brand",
].join(" ");

export const primaryButtonStyles = [
  "min-h-[54px] inline-flex items-center justify-center gap-[12px] py-[15px] px-[22px] rounded-[17px] text-[14px]",
  "[font-weight:750] no-underline [transition:background_0.18s,_box-shadow_0.18s] mobile:min-h-[53px]",
  "mobile:text-[13px] mobile:rounded-[15px] mobile-type:text-[14px] [[data-ui~=button]&]:[background:var(--blue)]",
  "[[data-ui~=button]&]:text-[white] [[data-ui~=button]&]:[box-shadow:0_6px_14px_#3d5af420]",
  "[[data-ui~=button]&:hover:not(:disabled)]:[background:var(--blue-dark)]",
  "[[data-ui~=button]&:hover:not(:disabled)]:[box-shadow:0_8px_18px_#3d5af42c]",
  "[[data-ui~=button]&_>_span:first-child]:[flex:1] [[data-ui~=button]&_>_span:first-child]:text-left",
  "[[data-ui~=onboarding-controls]_&]:w-full [[data-ui~=adventure-copy]_[data-ui~=button]&]:w-full",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&]:[background:#fff]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&]:text-ink",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&]:[box-shadow:0_5px_10px_#1423380d]",
  "mobile:[[data-ui~=adventure-copy]_[data-ui~=button]&]:text-[12px]",
  "mobile:[[data-ui~=adventure-copy]_[data-ui~=button]&]:min-h-[50px]",
  "mobile:[[data-ui~=adventure-copy]_[data-ui~=button]&]:rounded-[14px]",
  "mobile:[[data-ui~=adventure-copy]_[data-ui~=button]&]:py-[13px]",
  "mobile:[[data-ui~=adventure-copy]_[data-ui~=button]&]:px-[17px]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&:hover:not(:disabled)]:[background:#eef2ff]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&:hover:not(:disabled)]:text-[var(--blue-dark)]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&:hover:not(:disabled)]:[box-shadow:0_6px_16px_#14233824]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&:focus-visible]:[background:#eef2ff]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&:focus-visible]:text-[var(--blue-dark)]",
  "[[data-ui~=adventure-copy]_[data-ui~=button]&:focus-visible]:[box-shadow:0_6px_16px_#14233824]",
  "[[data-ui~=wizard-actions]_>_&]:w-full [[data-ui~=wizard-actions]_>_&]:text-[13px]",
  "mobile:[[data-ui~=wizard-actions]_>_&]:min-h-[54px] mobile:[[data-ui~=wizard-actions]_>_&]:rounded-[16px]",
  "mobile:[[data-ui~=wizard-actions]_>_&]:text-[12px] [[data-ui~=loading-page]_>_&]:w-full",
  "[[data-ui~=result-sticky]_>_&]:[flex:1] [[data-ui~=result-sticky]_>_&]:text-[12px]",
  "[[data-ui~=result-sticky]_>_&]:gap-[9px] mobile:[[data-ui~=result-sticky]_>_&]:text-[11px]",
  "mobile:[[data-ui~=result-sticky]_>_&]:min-h-[51px] mobile:[[data-ui~=result-sticky]_>_&]:py-[13px]",
  "mobile:[[data-ui~=result-sticky]_>_&]:px-[15px] mobile:[[data-ui~=result-sticky]_>_&]:gap-[8px]",
  "mobile:[[data-ui~=result-sticky]_>_&]:rounded-[14px] narrow:[[data-ui~=result-sticky]_>_&]:text-[11px]",
  "mobile-type:[[data-ui~=result-sticky]_>_&]:text-[14px]",
  "[[data-ui~=result-sticky]_>_&_>_span:first-child]:[flex:initial] [[data-ui~=empty-state]_>_&]:w-full",
  "[[data-ui~=empty-state]_>_&]:max-w-[300px] [[data-ui~=empty-state]_>_&]:mb-[7px]",
  "[[data-ui~=empty-state]_>_&]:text-[12px] mobile:[[data-ui~=empty-state]_>_&]:text-[12px]",
  "[[data-ui~=preset-actions]_&]:w-full [[data-ui~=screen-loading]_[data-ui~=has-error]_>_&]:mb-[8px]",
].join(" ");

export const selectedChoiceStyles = [
  "[[data-ui~=choice]&]:[background:#f1f4ff] [[data-ui~=choice]&]:[border-color:#8a9bfa]",
  "[[data-ui~=duration-card]&]:[background:#f2f5ff] [[data-ui~=duration-card]&]:[border-color:#8a9bfa]",
  "[[data-ui~=duration-card]&_>_span]:text-brand",
].join(" ");

export const softLavenderIconStyles = [
  "w-[47px] h-[47px] grid place-items-center rounded-[15px] shrink-0 tablet:[[data-ui~=how-card]_&]:h-[37px]",
  "tablet:[[data-ui~=how-card]_&]:w-[37px] tablet:[[data-ui~=how-card]_&]:rounded-[12px]",
  "mobile:[[data-ui~=how-card]_&]:h-[38px] mobile:[[data-ui~=how-card]_&]:w-[38px]",
  "mobile:[[data-ui~=how-card]_&]:rounded-[12px] mobile:[[data-ui~=section-title]_&]:h-[39px]",
  "mobile:[[data-ui~=section-title]_&]:w-[39px] mobile:[[data-ui~=section-title]_&]:rounded-[13px]",
  "mobile:[[data-ui~=map-button]_&]:w-[37px] mobile:[[data-ui~=map-button]_&]:h-[37px]",
  "mobile:[[data-ui~=map-button]_&]:rounded-[12px] mobile:[[data-ui~=saved-trip]_>_&]:h-[38px]",
  "mobile:[[data-ui~=saved-trip]_>_&]:w-[38px] mobile:[[data-ui~=saved-trip]_>_&]:rounded-[12px]",
  "mobile:[[data-ui~=about-info]_&]:w-[37px] mobile:[[data-ui~=about-info]_&]:h-[37px]",
  "mobile:[[data-ui~=about-info]_&]:rounded-[12px] [[data-ui~=soft-icon]&]:[background:#f2edff]",
  "[[data-ui~=soft-icon]&]:text-[#8a64d6]",
].join(" ");

export const wizardFieldLabelStyles = [
  "block text-[11px] [font-weight:750] leading-[1.6] mobile:text-[11px] mobile-type:text-[13px]",
  "[&_input]:mt-[9px] [&_input]:block [&_input]:w-full [&_input]:[border:1px_solid_#e6e9f0]",
  "[&_input]:[background:#fafbfe] [&_input]:rounded-[13px] [&_input]:p-[14px] [&_input]:text-[13px]",
  "[&_input]:text-ink [&_input]:min-h-[51px] mobile:[&_input]:text-[16px] mobile:[&_input]:min-h-[54px]",
  "mobile:[&_input]:[background:#fff] mobile:[&_input]:p-[14px] [&_textarea]:mt-[9px] [&_textarea]:block",
  "[&_textarea]:w-full [&_textarea]:[border:1px_solid_#e6e9f0] [&_textarea]:[background:#fafbfe]",
  "[&_textarea]:rounded-[13px] [&_textarea]:p-[14px] [&_textarea]:text-[13px] [&_textarea]:text-ink",
  "[&_textarea]:[resize:vertical] [&_textarea]:min-h-[92px] [&_textarea]:leading-[1.7]",
  "mobile:[&_textarea]:[background:#fff] mobile:[&_textarea]:p-[14px] mobile:[&_textarea]:text-[14px]",
  "mobile:[&_textarea]:min-h-[100px] [&_select]:mt-[9px] [&_select]:block [&_select]:w-full",
  "[&_select]:[border:1px_solid_#e6e9f0] [&_select]:[background:#fafbfe] [&_select]:rounded-[13px]",
  "[&_select]:p-[14px] [&_select]:text-[13px] [&_select]:text-ink [&_select]:min-h-[51px]",
  "mobile:[&_select]:text-[16px] mobile:[&_select]:min-h-[54px] mobile:[&_select]:[background:#fff]",
  "mobile:[&_select]:p-[14px] [&_input::placeholder]:text-[#a3a9b8] [&_input::placeholder]:text-[12px]",
  "mobile:[&_input::placeholder]:text-[12px] [&_textarea::placeholder]:text-[#a3a9b8]",
  "[&_textarea::placeholder]:text-[12px] mobile:[&_textarea::placeholder]:text-[12px]",
  "[[data-ui~=fields-pair]_&]:text-[11px] mobile:[[data-ui~=fields-pair]_&]:text-[11px]",
  "[[data-ui~=field-label]&]:mt-[24px]",
].join(" ");
