import {rem} from '@mantine/core';

interface AddressBookIconProps extends React.ComponentPropsWithoutRef<'svg'> {
    size?: number | string;
}

export function JenkinsIcon({size, style, ...others}: AddressBookIconProps) {
    return (
        <img
            style={{width: rem(size), height: rem(size), ...style}}
            src="/static/jenkins.svg"
        />
    );
}

export default JenkinsIcon;