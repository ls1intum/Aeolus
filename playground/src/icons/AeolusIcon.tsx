import {rem} from '@mantine/core';

interface AddressBookIconProps extends React.ComponentPropsWithoutRef<'svg'> {
    size?: number | string;
}

export function AeolusIcon({size, style, ...others}: AddressBookIconProps) {
    return (
        <img
            style={{width: rem(size), height: rem(size), ...style}}
            src="/static/aeolus.svg"
        />
    );
}

export default AeolusIcon;